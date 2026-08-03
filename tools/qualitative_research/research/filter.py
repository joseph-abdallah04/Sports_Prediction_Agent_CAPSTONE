"""Recency, round, and fixture relevance filtering + URL dedupe."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from .models import ResearchItem
from .queries import TEAM_SLUGS
from .timestamps import parse_published

_ROUND_RE = re.compile(r"\bround\s+(\d+)\b", re.I)

_NOISE_CATEGORY = {
    "fantasy",
    "tipping",
    "match highlights",
    "highlights",
}
_HISTORICAL_YEAR = re.compile(r"\b(19\d{2}|20[0-1]\d)\b")
_NFL_NOISE = re.compile(
    r"\b(nfl|super bowl|carolina panthers|training camp|nflpa)\b",
    re.I,
)

# Canonical NRL club tokens (longest first) for robust "X v Y" parsing
_CLUB_CANONICAL: list[str] = sorted(
    {
        *TEAM_SLUGS.keys(),
        "manly",  # Sea Eagles alias often used in headlines
        "tigers",
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
        aliases.update({"tigers", "wests tigers", "w.tigers"})
    if t == "sea eagles":
        aliases.update({"sea eagles", "eagles", "manly"})
    return aliases


def _mentions_team(text: str, team: str) -> bool:
    blob = _norm(text)
    return any(a in blob for a in _team_aliases(team) if len(a) > 2)


def _canonical_club(token: str) -> str:
    t = _norm(token)
    if t in {"tigers", "w.tigers"}:
        return "wests tigers"
    if t in {"eagles", "manly"}:
        return "sea eagles"
    return t


def _is_other_fixture_preview(title: str, home: str, away: str) -> bool:
    """True if title is clearly 'X v Y' for a different NRL pairing.

    Uses known club nicknames only so 'Eels vs Panthers Preview' is not
    misread as an other-fixture (old regex swallowed 'Preview…' into team 2).
    """
    m = _VS_KNOWN.search(title or "")
    if not m:
        return False
    a = _canonical_club(m.group(1))
    b = _canonical_club(m.group(2))
    home_aliases = {_canonical_club(x) for x in _team_aliases(home)}
    away_aliases = {_canonical_club(x) for x in _team_aliases(away)}
    ours = home_aliases | away_aliases
    title_pair = {a, b}
    if not title_pair & ours:
        return False
    # Exact fixture (order-independent)
    if (home_aliases & title_pair) and (away_aliases & title_pair):
        return False
    # Involves exactly one of our teams → different opponent
    mentions_home = bool(title_pair & home_aliases)
    mentions_away = bool(title_pair & away_aliases)
    return mentions_home ^ mentions_away


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
) -> tuple[list[ResearchItem], dict[str, int], list[dict[str, Any]]]:
    """Keep items relevant to this fixture / round within the time window.

    Also returns dropped source records for local debug logging only.
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

        # NFL / US sports colliding on "Panthers"
        if _NFL_NOISE.search(title_l) and "nrl" not in title_l:
            stats["dropped_noise"] += 1
            dropped.append(_drop_record(item, "dropped_noise_nfl"))
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

        mentions_home = _mentions_team(text_blob, home_team)
        mentions_away = _mentions_team(text_blob, away_team)
        is_league_wide = any(
            k in title_l for k in ("late mail", "casualty ward", "team list")
        ) or _is_league_round_roundup(item.title or "", round_number)

        if item.channel == "nrl_news":
            if is_league_wide:
                reasons.append("nrl_official_roundup")
                item.relevance_score += 2.5
            elif mentions_home and mentions_away:
                reasons.append("nrl_mentions_both")
                item.relevance_score += 2.0
            elif mentions_home or mentions_away:
                if any(k in title_l for k in ("as it happened", "live blog", "match report")):
                    if not (mentions_home and mentions_away):
                        stats["dropped_irrelevant"] += 1
                        dropped.append(_drop_record(item, "dropped_irrelevant_other_game_recap"))
                        continue
                reasons.append("nrl_club_news")
                item.relevance_score += 1.0
            else:
                stats["dropped_irrelevant"] += 1
                dropped.append(_drop_record(item, "dropped_irrelevant_no_team"))
                continue
        else:
            if not (mentions_home or mentions_away or is_league_wide):
                stats["dropped_irrelevant"] += 1
                dropped.append(_drop_record(item, "dropped_irrelevant_no_team"))
                continue
            if is_league_wide and not (mentions_home or mentions_away):
                reasons.append("league_round_roundup")
            else:
                reasons.append("mentions_fixture_team")

        if mentions_home and mentions_away:
            item.relevance_score += 2.0
            reasons.append("mentions_both_teams")
        if any(k in title_l for k in ("late mail", "casualty", "injury", "team list")):
            item.relevance_score += 1.5
            reasons.append("injury_or_team_list")
        if any(k in title_l or k in (item.snippet or "").lower() for k in _CONTEXT_CUES):
            item.relevance_score += 1.0
            reasons.append("contextual_factor")

        if item.source_tier == "official":
            item.relevance_score += 1.0
        elif item.source_tier == "unverified_community":
            item.relevance_score -= 0.5

        item.keep_reasons = reasons
        kept.append(item)
        stats["kept"] += 1

    kept.sort(key=lambda x: (-x.relevance_score, x.age_hours if x.age_hours is not None else 9999))
    return kept, stats, dropped
