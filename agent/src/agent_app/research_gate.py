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

    has_official = False
    has_availability = False
    for i in with_body:
        tier = (i.get("source_tier") or "").lower()
        channel = (i.get("channel") or "").lower()
        if tier == "official" or channel == "nrl_news":
            has_official = True
        blob = " ".join(
            [
                i.get("title") or "",
                i.get("snippet") or "",
                i.get("body_excerpt") or "",
            ]
        )
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

    trust_or_avail = has_official or has_availability
    ok = kept_with_body >= 3 and trust_or_avail and not every_wide_failed

    diag = {
        "kept_items_with_body": kept_with_body,
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
        if not trust_or_avail:
            reasons.append("missing_official_and_availability_signal")
        if every_wide_failed:
            reasons.append("all_wide_net_channels_failed")
        diag["fail_reasons"] = reasons
    return ok, diag
