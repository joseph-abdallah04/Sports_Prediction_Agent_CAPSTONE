"""Recency, round, and fixture relevance filtering + URL dedupe."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from .models import ResearchItem
from .queries import REGION_ALIAS_TO_NICKNAME, TEAM_SLUGS, region_aliases
from .timestamps import parse_published

_ROUND_RE = re.compile(r"\bround\s+(\d+)\b", re.I)

_NOISE_CATEGORY = {
    "fantasy",
    "tipping",
    "match highlights",
    "highlights",
}
_HISTORICAL_YEAR = re.compile(r"\b(19\d{2}|20[0-1]\d)\b")
# US sports share nicknames with NRL clubs (Dallas Cowboys, Carolina Panthers).
# Only applied when the headline has no rugby league marker.
_US_SPORTS_NOISE = re.compile(
    r"\b("
    r"nfl|nflpa|super bowl|training camp|"
    r"nba|wnba|mlb|nhl|ncaa|"
    r"dallas cowboys|carolina panthers"
    r")\b",
    re.I,
)
_LEAGUE_MARKER = re.compile(r"\b(nrl|rugby league|premiership|telstra)\b", re.I)
# Paths that only appear on rugby league coverage, for outlets that also cover
# other codes (foxsports.com.au/nrl/…, smh.com.au/sport/nrl/…).
_LEAGUE_URL = re.compile(r"(^|[/._-])(nrl|rugby-?league)([/._-]|$)", re.I)

# Canonical NRL club tokens (longest first) for robust "X v Y" parsing.
# Includes city/region names so "Gold Coast v North Queensland" is recognised.
_CLUB_CANONICAL: list[str] = sorted(
    {
        *TEAM_SLUGS.keys(),
        *REGION_ALIAS_TO_NICKNAME.keys(),
    },
    key=len,
    reverse=True,
)
_CLUB_RE = "|".join(re.escape(c) for c in _CLUB_CANONICAL)
_VS_KNOWN = re.compile(
    rf"\b({_CLUB_RE})\s+v(?:s\.?)?\s+({_CLUB_RE})\b",
    re.I,
)

# Boost cues for qualitative factors only. Weather / venue / referee are owned
# by fixture_scene — do not prefer articles that are mainly about those.
_CONTEXT_CUES = (
    "travel",
    "form",
    "motivation",
    "must win",
    "must-win",
    "suspension",
    "judiciary",
    "sin bin",
    "line movement",
    "odds",
)

_LEAGUE_ROUNDUP_CUES = (
    "tips",
    "predictions",
    "odds",
    "teams",
    "team list",
    "line-up",
    "lineup",
    "line-ups",
    "lineups",
    "everything you need",
    "fixtures",
    "early mail",
    "late mail",
    "casualty ward",
)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _team_aliases(team: str) -> set[str]:
    t = _norm(team)
    aliases = {t}
    parts = t.split()
    if parts:
        aliases.add(parts[-1])
    if t == "wests tigers":
        aliases.add("w.tigers")
    aliases.update(region_aliases(t))
    return aliases


def _mentions_team(text: str, team: str) -> bool:
    blob = _norm(text)
    return any(a in blob for a in _team_aliases(team) if len(a) > 2)


def _has_league_signal(item: ResearchItem, text_blob: str) -> bool:
    """True if anything about this item says 'rugby league' rather than a nickname.

    Half the NRL's nicknames belong to other clubs in other codes — Tennessee
    Titans, Dallas Cowboys, Carolina Panthers — and one belongs to a film. A
    nickname match alone is not evidence, so we look for a league marker in the
    text, in the URL path, or in the provenance of the item itself.
    """
    if item.channel == "nrl_news" or item.source_tier == "official":
        return True
    if _LEAGUE_MARKER.search(text_blob):
        return True
    return bool(_LEAGUE_URL.search(item.url or ""))


def _canonical_club(token: str) -> str:
    t = _norm(token)
    if t in {"tigers", "w.tigers"}:
        return "wests tigers"
    return REGION_ALIAS_TO_NICKNAME.get(t, t)


_LIVE_COVERAGE = ("as it happened", "live blog", "live scores", "match report")

# Evergreen nrl.com Casualty Ward hub that republishes under a January 2026 URL.
_EVERGREEN_CASUALTY_WARD = re.compile(
    r"nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026",
    re.I,
)

# League-wide round wraps kept in the final pack (Late Mail / tips / team lists
# that are not a dedicated club page for this fixture).
MAX_LEAGUE_ROUNDUPS = 2
_ROUNDUP_REASONS = frozenset(
    {
        "nrl_official_roundup",
        "league_round_roundup",
    }
)


def _is_live_coverage(title: str) -> bool:
    title_l = (title or "").lower()
    return any(k in title_l for k in _LIVE_COVERAGE)


def _is_evergreen_casualty_ward(url: str) -> bool:
    return bool(_EVERGREEN_CASUALTY_WARD.search(url or ""))


def _is_other_fixture_preview(title: str, home: str, away: str) -> bool:
    """True if title is clearly 'X v Y' for a different NRL pairing.

    Uses known club nicknames only so 'Eels vs Panthers Preview' is not
    misread as an other-fixture (old regex swallowed 'Preview…' into team 2).
    Any known pairing that is not this fixture is dropped — including tips
    pages that name two other clubs and never mention ours.
    """
    m = _VS_KNOWN.search(title or "")
    if not m:
        return False
    a = _canonical_club(m.group(1))
    b = _canonical_club(m.group(2))
    home_aliases = {_canonical_club(x) for x in _team_aliases(home)}
    away_aliases = {_canonical_club(x) for x in _team_aliases(away)}
    title_pair = {a, b}
    # Exact fixture (order-independent)
    if (home_aliases & title_pair) and (away_aliases & title_pair):
        return False
    return True


def _is_league_round_roundup(title: str, round_number: int | None) -> bool:
    """Round-wide tips/teams/odds pieces that omit club names in the title."""
    if round_number is None:
        return False
    if extract_round(title) != round_number:
        return False
    title_l = (title or "").lower()
    return any(k in title_l for k in _LEAGUE_ROUNDUP_CUES)


def extract_round(text: str) -> int | None:
    m = _ROUND_RE.search(text or "")
    return int(m.group(1)) if m else None


def dedupe_by_url(items: list[ResearchItem]) -> list[ResearchItem]:
    seen: set[str] = set()
    out: list[ResearchItem] = []
    for item in items:
        key = item.url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def canonical_url(url: str) -> str:
    """Normalize publisher URLs for post-resolve dedupe."""
    u = (url or "").strip()
    if not u:
        return u
    # Drop query/fragment; lowercase host+path
    u = u.split("#", 1)[0].split("?", 1)[0].rstrip("/").lower()
    return u


def _item_rank(item: ResearchItem) -> tuple:
    """Higher is better when choosing which duplicate to keep."""
    official = 1 if item.source_tier == "official" or item.channel == "nrl_news" else 0
    body_len = len(item.body_excerpt or "")
    return (official, item.relevance_score, body_len)


def dedupe_by_canonical_url(
    items: list[ResearchItem],
) -> tuple[list[ResearchItem], list[dict[str, Any]]]:
    """Keep one item per resolved publisher URL (prefer official / richer body).

    Returns (deduped_items, drop_records for local audit).
    """
    best: dict[str, ResearchItem] = {}
    order: list[str] = []
    for item in items:
        key = canonical_url(item.url)
        if not key:
            key = item.url
        if key not in best:
            best[key] = item
            order.append(key)
            continue
        if _item_rank(item) > _item_rank(best[key]):
            best[key] = item

    kept = [best[k] for k in order]
    kept_ids = {id(i) for i in kept}
    dropped_recs: list[dict[str, Any]] = []
    for item in items:
        if id(item) in kept_ids:
            continue
        dropped_recs.append(
            {
                "reason": "dropped_duplicate_url",
                "channel": item.channel,
                "source_tier": item.source_tier,
                "title": item.title,
                "url": item.url,
                "published_at": item.published_at,
                "category": item.category,
            }
        )
    return kept, dropped_recs


def _drop_record(item: ResearchItem, reason: str) -> dict[str, Any]:
    return {
        "reason": reason,
        "channel": item.channel,
        "source_tier": item.source_tier,
        "title": item.title,
        "url": item.url,
        "published_at": item.published_at,
        "category": item.category,
    }


def filter_items(
    items: list[ResearchItem],
    *,
    home_team: str,
    away_team: str,
    kickoff: datetime,
    round_number: int | None = None,
    max_age_days: int = 10,
    now: datetime | None = None,
) -> tuple[
    list[ResearchItem], dict[str, int], list[dict[str, Any]], list[ResearchItem]
]:
    """Keep items relevant to this fixture / round within the time window.

    Returns (kept, stats, dropped, deferred). ``deferred`` items passed every
    structural gate but showed no fixture team in the text available before
    body fetch; pass them to :func:`promote_deferred_with_bodies` afterwards.
    ``dropped`` records are for local debug logging only.
    """
    now = now or datetime.now(timezone.utc)
    window_start = kickoff.astimezone(timezone.utc) - timedelta(days=max_age_days)
    window_end = kickoff.astimezone(timezone.utc) + timedelta(days=1)

    stats = {
        "dropped_stale": 0,
        "dropped_wrong_round": 0,
        "dropped_noise": 0,
        "dropped_irrelevant": 0,
        "kept": 0,
    }
    kept: list[ResearchItem] = []
    dropped: list[dict[str, Any]] = []
    deferred: list[ResearchItem] = []

    for item in items:
        reasons: list[str] = []
        text_blob = " ".join(
            filter(None, [item.title, item.snippet or "", item.body_excerpt or "", item.category or ""])
        )
        cat = (item.category or "").strip().lower()
        title_l = (item.title or "").lower()

        if cat in _NOISE_CATEGORY or "highlight" in cat or "highlight" in title_l:
            stats["dropped_noise"] += 1
            dropped.append(_drop_record(item, "dropped_noise"))
            continue

        hy = _HISTORICAL_YEAR.search(item.title or "")
        if hy and int(hy.group(1)) < kickoff.year - 1:
            stats["dropped_noise"] += 1
            dropped.append(_drop_record(item, "dropped_noise_historical_year"))
            continue

        if re.search(r"\bnrlw\b", title_l) or re.search(r"\bnrlw\b", cat):
            stats["dropped_noise"] += 1
            dropped.append(_drop_record(item, "dropped_noise_nrlw"))
            continue

        # US sports colliding on shared nicknames ("Cowboys", "Panthers")
        if _US_SPORTS_NOISE.search(title_l) and not _LEAGUE_MARKER.search(title_l):
            stats["dropped_noise"] += 1
            dropped.append(_drop_record(item, "dropped_noise_us_sports"))
            continue

        if _is_other_fixture_preview(item.title or "", home_team, away_team):
            stats["dropped_irrelevant"] += 1
            dropped.append(_drop_record(item, "dropped_irrelevant_other_fixture"))
            continue

        pub = parse_published(item.published_at, now=now) if item.published_at else None
        if pub is not None:
            if pub < window_start or pub > window_end:
                stats["dropped_stale"] += 1
                dropped.append(_drop_record(item, "dropped_stale"))
                continue
            item.published_at = pub.astimezone(timezone.utc).isoformat()
            item.age_hours = (now - pub).total_seconds() / 3600.0
            reasons.append("in_time_window")
        else:
            if item.source_tier != "official":
                stats["dropped_stale"] += 1
                dropped.append(_drop_record(item, "dropped_stale_no_date"))
                continue
            if not any(k in title_l for k in ("late mail", "casualty ward")):
                stats["dropped_stale"] += 1
                dropped.append(_drop_record(item, "dropped_stale_no_date"))
                continue
            reasons.append("no_date_but_official_roundup")

        title_round = extract_round(item.title)
        if round_number is not None and title_round is not None:
            if title_round != round_number:
                stats["dropped_wrong_round"] += 1
                dropped.append(_drop_record(item, "dropped_wrong_round"))
                continue
            reasons.append(f"round_{round_number}_match")
            item.relevance_score += 3.0

        verdict, drop_reason = _apply_relevance(
            item,
            text_blob=text_blob,
            title_l=title_l,
            home_team=home_team,
            away_team=away_team,
            round_number=round_number,
            reasons=reasons,
        )
        if verdict == "drop":
            stats["dropped_irrelevant"] += 1
            dropped.append(_drop_record(item, drop_reason))
            continue
        if verdict == "defer":
            # Team names frequently appear only in the article body, which has
            # not been fetched at this point. Hold the item for a second pass
            # once bodies exist rather than discarding it on the title alone.
            item.keep_reasons = reasons
            deferred.append(item)
            continue

        item.keep_reasons = reasons
        kept.append(item)
        stats["kept"] += 1

    stats["deferred_pending_body"] = len(deferred)
    kept.sort(key=sort_key)
    deferred.sort(key=sort_key)
    return kept, stats, dropped, deferred


def sort_key(item: ResearchItem) -> tuple:
    return (
        -item.relevance_score,
        item.age_hours if item.age_hours is not None else 9999,
    )


def _apply_relevance(
    item: ResearchItem,
    *,
    text_blob: str,
    title_l: str,
    home_team: str,
    away_team: str,
    round_number: int | None,
    reasons: list[str],
) -> tuple[str, str]:
    """Team-relevance gate plus relevance scoring.

    Returns (verdict, drop_reason) where verdict is keep / defer / drop.
    "defer" means the item looks structurally fine but no fixture team was
    found in the text available so far.
    """
    if not _has_league_signal(item, text_blob):
        # Defer rather than drop on the first pass: the title and snippet are
        # often too thin to carry a league marker that the body does carry.
        if (item.body_excerpt or "").strip():
            return "drop", "dropped_irrelevant_not_rugby_league"
        return "defer", ""

    mentions_home = _mentions_team(text_blob, home_team)
    mentions_away = _mentions_team(text_blob, away_team)
    is_league_wide = any(
        k in title_l for k in ("late mail", "casualty ward", "team list")
    ) or _is_league_round_roundup(item.title or "", round_number)

    if item.channel == "nrl_news":
        if is_league_wide:
            if mentions_home and mentions_away:
                reasons.append("nrl_official_roundup_on_fixture")
                item.relevance_score += 1.0
            else:
                reasons.append("nrl_official_roundup")
                item.relevance_score += 0.5
        elif mentions_home and mentions_away:
            reasons.append("nrl_mentions_both")
            item.relevance_score += 2.0
        elif mentions_home or mentions_away:
            if _is_live_coverage(item.title or "") and not (
                mentions_home and mentions_away
            ):
                return "drop", "dropped_irrelevant_other_game_recap"
            reasons.append("nrl_club_news")
            item.relevance_score += 1.0
        else:
            return "defer", ""
    else:
        if not (mentions_home or mentions_away or is_league_wide):
            return "defer", ""
        if is_league_wide and not (mentions_home or mentions_away):
            reasons.append("league_round_roundup")
        else:
            reasons.append("mentions_fixture_team")

    if mentions_home and mentions_away:
        item.relevance_score += 3.0
        reasons.append("mentions_both_teams")
    # Title bonus only when the article is actually about this fixture.
    if (mentions_home or mentions_away) and any(
        k in title_l for k in ("late mail", "casualty", "injury", "team list")
    ):
        item.relevance_score += 1.5
        reasons.append("injury_or_team_list")
    if any(k in title_l or k in (item.snippet or "").lower() for k in _CONTEXT_CUES):
        item.relevance_score += 1.0
        reasons.append("contextual_factor")

    if item.source_tier == "official":
        item.relevance_score += 1.0
    elif item.source_tier == "unverified_community":
        item.relevance_score -= 0.5

    if _is_live_coverage(item.title or ""):
        item.relevance_score -= 2.0
        reasons.append("live_coverage_penalty")

    return "keep", ""


def promote_deferred_with_bodies(
    deferred: list[ResearchItem],
    *,
    home_team: str,
    away_team: str,
    round_number: int | None = None,
) -> tuple[list[ResearchItem], list[dict[str, Any]]]:
    """Second relevance pass for deferred items, now that bodies are attached.

    An article that only names the fixture teams in its body (common for
    official club pages and round wraps) is recovered here instead of being
    lost to a title-only relevance check.
    """
    promoted: list[ResearchItem] = []
    dropped: list[dict[str, Any]] = []

    for item in deferred:
        if not (item.body_excerpt or "").strip():
            dropped.append(_drop_record(item, "dropped_irrelevant_no_team"))
            continue
        text_blob = " ".join(
            filter(
                None,
                [
                    item.title,
                    item.snippet or "",
                    item.body_excerpt or "",
                    item.category or "",
                ],
            )
        )
        reasons = list(item.keep_reasons or [])
        verdict, drop_reason = _apply_relevance(
            item,
            text_blob=text_blob,
            title_l=(item.title or "").lower(),
            home_team=home_team,
            away_team=away_team,
            round_number=round_number,
            reasons=reasons,
        )
        if verdict != "keep":
            dropped.append(
                _drop_record(item, drop_reason or "dropped_irrelevant_no_team")
            )
            continue
        reasons.append("promoted_after_body_fetch")
        item.keep_reasons = reasons
        promoted.append(item)

    promoted.sort(key=sort_key)
    return promoted, dropped


def _item_text(item: ResearchItem) -> str:
    return " ".join(
        filter(
            None,
            [
                item.title,
                item.snippet or "",
                item.body_excerpt or "",
                item.category or "",
            ],
        )
    )


def _structural_reasons(reasons: list[str] | None) -> list[str]:
    keep = []
    for r in reasons or []:
        if r.startswith("round_") and r.endswith("_match"):
            keep.append(r)
        elif r in (
            "in_time_window",
            "no_date_but_official_roundup",
            "promoted_after_body_fetch",
        ):
            keep.append(r)
    return keep


def cap_league_roundups(
    items: list[ResearchItem],
    *,
    max_roundups: int = MAX_LEAGUE_ROUNDUPS,
) -> tuple[list[ResearchItem], list[dict[str, Any]]]:
    """Keep at most ``max_roundups`` league-wide wraps; prefer higher scores."""
    kept: list[ResearchItem] = []
    dropped: list[dict[str, Any]] = []
    n_roundups = 0
    for item in items:
        is_roundup = bool(set(item.keep_reasons or []) & _ROUNDUP_REASONS)
        if is_roundup:
            if n_roundups >= max_roundups:
                dropped.append(_drop_record(item, "dropped_roundup_cap"))
                continue
            n_roundups += 1
        kept.append(item)
    return kept, dropped


def refine_kept_after_bodies(
    items: list[ResearchItem],
    *,
    home_team: str,
    away_team: str,
    round_number: int | None = None,
) -> tuple[list[ResearchItem], list[dict[str, Any]]]:
    """Drop empty roundups / evergreen Casualty Ward, then rescore with bodies.

    Pass 1 ranking only sees titles. After fetch, a round wrap that never names
    this fixture is junk, and a Late Mail that *does* name both clubs should
    be scored as on-fixture rather than as a generic roundup.
    """
    kept: list[ResearchItem] = []
    dropped: list[dict[str, Any]] = []

    for item in items:
        if _is_evergreen_casualty_ward(item.url or ""):
            dropped.append(_drop_record(item, "dropped_evergreen_casualty_ward"))
            continue

        text_blob = _item_text(item)
        mentions_home = _mentions_team(text_blob, home_team)
        mentions_away = _mentions_team(text_blob, away_team)
        title_l = (item.title or "").lower()
        is_league_wide_title = any(
            k in title_l for k in ("late mail", "casualty ward", "team list")
        ) or _is_league_round_roundup(item.title or "", round_number)
        if is_league_wide_title and not mentions_home and not mentions_away:
            dropped.append(_drop_record(item, "dropped_roundup_no_fixture_team"))
            continue

        structural = _structural_reasons(item.keep_reasons)
        item.relevance_score = (
            3.0
            if any(r.startswith("round_") and r.endswith("_match") for r in structural)
            else 0.0
        )
        reasons = list(structural)
        verdict, drop_reason = _apply_relevance(
            item,
            text_blob=text_blob,
            title_l=title_l,
            home_team=home_team,
            away_team=away_team,
            round_number=round_number,
            reasons=reasons,
        )
        if verdict != "keep":
            dropped.append(
                _drop_record(item, drop_reason or "dropped_irrelevant_after_body")
            )
            continue
        item.keep_reasons = reasons
        kept.append(item)

    kept.sort(key=sort_key)
    kept, cap_drops = cap_league_roundups(kept)
    dropped.extend(cap_drops)
    return kept, dropped
