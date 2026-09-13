"""Local-only debug writers (not part of tool response or day cache)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DROPPED_DIR = PACKAGE_ROOT / "debug" / "dropped"


def write_dropped_sources(
    key: str,
    *,
    request: dict[str, Any],
    filter_summary: dict[str, int],
    dropped: list[dict[str, Any]],
) -> Path:
    """Write dropped source audit file for human review.

    Path: qualitative_research/debug/dropped/{cache_key}.json
    Never included in ResearchResponse or the day cache.
    """
    DROPPED_DIR.mkdir(parents=True, exist_ok=True)
    path = DROPPED_DIR / f"{key}.json"
    payload = {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "cache_key": key,
        "request": request,
        "filter_summary": filter_summary,
        "dropped_count": len(dropped),
        "dropped_sources": dropped,
    }
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    tmp.replace(path)
    logger.info("Wrote dropped_sources audit -> %s (%d items)", path.name, len(dropped))
    return path
