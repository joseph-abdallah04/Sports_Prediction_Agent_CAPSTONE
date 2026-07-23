"""Day-expiry disk cache for research responses."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = PACKAGE_ROOT / "cache"
AU_TZ = ZoneInfo("Australia/Sydney")


def cache_key(
    home_team: str,
    away_team: str,
    kickoff_date: str,
    round_number: int | None,
) -> str:
    raw = "|".join(
        [
            home_team.strip().lower(),
            away_team.strip().lower(),
            kickoff_date,
            str(round_number if round_number is not None else ""),
        ]
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _today_au() -> date:
    return datetime.now(AU_TZ).date()


def cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def load(key: str) -> dict | None:
    path = cache_path(key)
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
        logger.info("Cache expired for %s (expires_on=%s)", key, expires_on)
        return None
    return payload.get("response")


def save(key: str, response: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Valid through end of today AU; next calendar day forces refresh.
    payload = {
        "expires_on": _today_au().isoformat(),
        "saved_at": datetime.now(AU_TZ).isoformat(),
        "response": response,
    }
    path = cache_path(key)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    tmp.replace(path)
    logger.info("Cached research response -> %s", path.name)
