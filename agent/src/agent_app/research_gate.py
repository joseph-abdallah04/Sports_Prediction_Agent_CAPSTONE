"""Deterministic research coverage gate (Loop A)."""

from __future__ import annotations

import re
from typing import Any

_AVAILABILITY_RE = re.compile(
    r"\b("
    r"injury|injuries|injured|sidelined|late mail|early mail|"
    r"team list|team lists|line-?up|lineup|casualty|suspension|"
    r"suspended|judiciary|doubtful|ruled out"
    r")\b",
    re.I,
)

MIN_BOTH_TEAMS_ITEMS = 3


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _team_aliases(team: str) -> set[str]:
    t = _norm(team)
    aliases = {t}
    parts = t.split()
    if parts:
        aliases.add(parts[-1])
    if t == "wests tigers":
        aliases.update({"tigers", "w.tigers"})
    return {a for a in aliases if len(a) > 2}


def _mentions_team(text: str, team: str) -> bool:
    blob = _norm(text)
    return any(a in blob for a in _team_aliases(team))


def _item_blob(item: dict[str, Any]) -> str:
    return " ".join(
        [
            item.get("title") or "",
            item.get("snippet") or "",
            item.get("body_excerpt") or "",
        ]
    )


def research_ok(research: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Return (ok, diagnostics). Soft-fail research still evaluated."""
    if research.get("error"):
        return False, {"reason": "research_error", "detail": research.get("detail")}

    items = research.get("items") or []
    with_body = [
        i
        for i in items
        if isinstance(i, dict) and (i.get("body_excerpt") or "").strip()
    ]
    kept_with_body = len(with_body)

    request = research.get("request") or {}
    home = request.get("home_team") or ""
    away = request.get("away_team") or ""

    both_teams = []
    fixture_availability = False
    for i in with_body:
        blob = _item_blob(i)
        if home and away and _mentions_team(blob, home) and _mentions_team(blob, away):
            both_teams.append(i)
            if _AVAILABILITY_RE.search(blob):
                fixture_availability = True

    both_teams_count = len(both_teams)

    has_official = False
    has_availability = False
    for i in with_body:
        tier = (i.get("source_tier") or "").lower()
        channel = (i.get("channel") or "").lower()
        if tier == "official" or channel == "nrl_news":
            has_official = True
        blob = _item_blob(i)
        if _AVAILABILITY_RE.search(blob):
            has_availability = True

    channels = research.get("channels") or {}
    wide = ("duckduckgo", "google_news_rss", "nrl_news")
    statuses = []
    for name in wide:
        ch = channels.get(name) or {}
        statuses.append(
            {
                "name": name,
                "status": ch.get("status"),
                "items_kept": ch.get("items_kept", 0),
            }
        )
    every_wide_failed = all(
        (s["status"] in {"error", "rate_limited"} and (s["items_kept"] or 0) == 0)
        for s in statuses
    ) and len(statuses) == 3

    enough_on_fixture = both_teams_count >= MIN_BOTH_TEAMS_ITEMS
    trust_or_avail = has_official or has_availability
    ok = (
        kept_with_body >= 3
        and enough_on_fixture
        and fixture_availability
        and trust_or_avail
        and not every_wide_failed
    )

    diag = {
        "kept_items_with_body": kept_with_body,
        "items_mentioning_both_teams": both_teams_count,
        "has_fixture_availability": fixture_availability,
        "has_official_or_nrl_news": has_official,
        "has_availability_keyword_hit": has_availability,
        "every_wide_net_channel_failed_with_zero_items": every_wide_failed,
        "channel_statuses": statuses,
        "research_ok": ok,
    }
    if not ok:
        reasons = []
        if kept_with_body < 3:
            reasons.append("insufficient_items_with_body")
        if not enough_on_fixture:
            reasons.append("insufficient_items_mentioning_both_teams")
        if not fixture_availability:
            reasons.append("missing_fixture_availability")
        if not trust_or_avail:
            reasons.append("missing_official_and_availability_signal")
        if every_wide_failed:
            reasons.append("all_wide_net_channels_failed")
        diag["fail_reasons"] = reasons
    return ok, diag
