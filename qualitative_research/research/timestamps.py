"""Parse relative / absolute publish timestamps from news UIs."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from zoneinfo import ZoneInfo

AU_TZ = ZoneInfo("Australia/Sydney")

_RELATIVE = re.compile(
    r"^\s*(?:about\s+)?(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago\s*$",
    re.I,
)
_YESTERDAY = re.compile(r"^\s*yesterday\s*$", re.I)


def parse_published(value: str | None, *, now: datetime | None = None) -> datetime | None:
    """Best-effort parse of ISO, RFC2822, or relative strings like '2 hours ago'."""
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    # ISO-8601 durations (video length) are not publish times
    if text.startswith("PT") and "T" in text[1:]:
        return None
    if re.fullmatch(r"PT[\dHMS.]+", text, re.I):
        return None
    now = now or datetime.now(timezone.utc)

    # ISO-ish
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=AU_TZ)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass

    # RFC 2822 (RSS)
    try:
        dt = parsedate_to_datetime(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass

    if _YESTERDAY.match(text):
        return (now.astimezone(AU_TZ) - timedelta(days=1)).astimezone(timezone.utc)

    m = _RELATIVE.match(text)
    if m:
        n = int(m.group(1))
        unit = m.group(2).lower()
        delta = {
            "second": timedelta(seconds=n),
            "minute": timedelta(minutes=n),
            "hour": timedelta(hours=n),
            "day": timedelta(days=n),
            "week": timedelta(weeks=n),
            "month": timedelta(days=30 * n),
            "year": timedelta(days=365 * n),
        }[unit]
        return (now - delta).astimezone(timezone.utc)

    return None


def to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()
