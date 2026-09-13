"""Day-expiry disk cache for scene responses (Australia/Sydney calendar day)."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import TOOL_VERSION

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PACKAGE_ROOT / "cache"
AU_TZ = ZoneInfo("Australia/Sydney")


def cache_key(
    home_team: str,
    away_team: str,
    season: int | None,
    round_number: int | None,
) -> str:
    # Versioned so a response-shape change never serves a stale-shaped hit.
    raw = "|".join(
        [
            TOOL_VERSION,
            home_team.strip().lower(),
            away_team.strip().lower(),
            str(season if season is not None else ""),
            str(round_number if round_number is not None else ""),
        ]
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _today_au() -> date:
    return datetime.now(AU_TZ).date()


def load(key: str) -> dict | None:
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Corrupt cache %s: %s", path, e)
        return None
    expires_on = payload.get("expires_on")
    if not expires_on:
        return None
    try:
        exp = date.fromisoformat(expires_on)
    except ValueError:
        return None
    if _today_au() > exp:
        logger.info("Cache expired for %s", key)
        return None
    return payload.get("response")


def save(key: str, response: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "expires_on": _today_au().isoformat(),
        "saved_at": datetime.now(AU_TZ).isoformat(),
        "response": response,
    }
    path = CACHE_DIR / f"{key}.json"
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    tmp.replace(path)
    logger.info("Cached scene response -> %s", path.name)
