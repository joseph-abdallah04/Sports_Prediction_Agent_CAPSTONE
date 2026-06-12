"""Validates the raw data lake after a backfill run.

Checks every saved match file for the structures the feature engineering
phase (Overview.md Phase 2) depends on:
  - match.stats.groups   (team telemetry: possession, attack, defence...)
  - match.timeline       (momentum/fatigue parsing via gameSeconds)
  - match.homeTeam/awayTeam players + score (labels and roster workload)

Usage:
    uv run python -m historical_data_backfill_etl.validate
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
RAW_HISTORICAL_DIR = ENGINE_ROOT / "data_lake" / "raw_historical"

REQUIRED_CHECKS = {
    "stats.groups": lambda m: bool(m.get("stats", {}).get("groups")),
    "stats.players": lambda m: bool(m.get("stats", {}).get("players", {}).get("homeTeam")),
    "timeline": lambda m: bool(m.get("timeline")),
    "scores": lambda m: (
        m.get("homeTeam", {}).get("score") is not None
        and m.get("awayTeam", {}).get("score") is not None
    ),
    "weather": lambda m: bool(m.get("weather")),
    "venue": lambda m: bool(m.get("venue")),
}


def main() -> int:
    files = sorted(RAW_HISTORICAL_DIR.glob("*/nrl_match_*.json"))
    if not files:
        print(f"No match files found under {RAW_HISTORICAL_DIR}")
        return 1

    per_season_counts: dict[str, int] = defaultdict(int)
    per_season_issues: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    unreadable: list[str] = []

    for path in files:
        season = path.parent.name
        per_season_counts[season] += 1
        try:
            with open(path, encoding="utf-8") as f:
                match = json.load(f).get("match", {})
        except (json.JSONDecodeError, OSError):
            unreadable.append(str(path))
            continue

        for check_name, check in REQUIRED_CHECKS.items():
            if not check(match):
                per_season_issues[season][check_name] += 1

    print(f"{'Season':<8} {'Files':>6}  Missing fields")
    print("-" * 60)
    for season in sorted(per_season_counts):
        issues = per_season_issues.get(season, {})
        issue_str = (
            ", ".join(f"{k}: {v}" for k, v in sorted(issues.items())) if issues else "none"
        )
        print(f"{season:<8} {per_season_counts[season]:>6}  {issue_str}")

    total = sum(per_season_counts.values())
    print("-" * 60)
    print(f"Total match files: {total}")
    if unreadable:
        print(f"Unreadable files ({len(unreadable)}):")
        for path in unreadable:
            print(f"  {path}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
