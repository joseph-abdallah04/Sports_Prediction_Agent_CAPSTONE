"""Where run output goes, and what it is called.

Output is organised so a human can find a run without opening anything:

    agent_runs/
      README.md                                  what all of this is
      fixtures/
        2026-R23_Titans-v-Cowboys/               one folder per fixture
          20260803T093203Z/                      one folder per run of it
            ledger.json                          complete, unabridged record
            summary.md                           the same run, readable
      rounds/
        2026-R23/
          predictions.json                       written BEFORE kickoff
          scored.json                            written AFTER the games
          summary.md                             the scorecard, readable

Fixture first, then run time, because the question people actually ask is
"what did it say about this game, and did that change between runs".
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")
_AU_TZ = ZoneInfo("Australia/Sydney")


def slug(text: str) -> str:
    """Filesystem-safe fragment that a human can still read."""
    cleaned = _UNSAFE.sub("-", (text or "").strip()).strip("-")
    return cleaned or "unknown"


def fixture_label(
    home_team: str,
    away_team: str,
    season: int | None = None,
    round_number: int | None = None,
) -> str:
    """e.g. '2026-R23_Titans-v-Cowboys', degrading gracefully if unknown.

    Season defaults to the current NRL season, matching what the scene tool
    assumes when the CLI omits it, so a run that fails before the scene
    resolves still files itself under the right season rather than losing it.
    """
    season = season or datetime.now(_AU_TZ).year
    parts = []
    if season and round_number:
        parts.append(f"{season}-R{round_number}")
    elif round_number:
        parts.append(f"R{round_number}")
    elif season:
        parts.append(str(season))
    parts.append(f"{slug(home_team)}-v-{slug(away_team)}")
    return "_".join(parts)


def fixture_run_dir(
    runs_root: Path,
    run_id: str,
    home_team: str,
    away_team: str,
    season: int | None = None,
    round_number: int | None = None,
) -> Path:
    """Directory for one run of one fixture."""
    label = fixture_label(home_team, away_team, season, round_number)
    # run_id is '<timestamp>-<short uuid>'; the timestamp alone sorts correctly
    # and is enough to disambiguate inside a fixture folder.
    stamp = run_id.split("-", 1)[0] if "-" in run_id else run_id
    return Path(runs_root) / "fixtures" / label / stamp


def round_dir(runs_root: Path, season: int, round_number: int) -> Path:
    """Directory for a whole-round prediction and its scorecard."""
    return Path(runs_root) / "rounds" / f"{season}-R{round_number}"
