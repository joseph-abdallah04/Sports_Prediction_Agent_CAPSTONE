"""CLI: research an upcoming NRL fixture.

Usage:
    uv run python -m research.cli --home Broncos --away Storm \\
        --kickoff 2026-07-25T19:30:00+10:00 --round 21
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow `uv run python -m research.cli` from qualitative_research/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research import TOOL_NAME
from research.assemble import research_fixture
from research.ledger_types import append_tool_record, make_tool_call_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualitative research for an NRL fixture")
    parser.add_argument("--home", required=True)
    parser.add_argument("--away", required=True)
    parser.add_argument("--kickoff", required=True, help="ISO kickoff datetime")
    parser.add_argument("--round", type=int, default=None, dest="round_number")
    parser.add_argument(
        "--venue",
        default=None,
        help="Optional echo only; not used in search (fixture_scene owns venue/weather/refs)",
    )
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--max-age-days", type=int, default=10)
    parser.add_argument(
        "--reddit",
        action="store_true",
        help="Also query r/nrl (off by default: near-zero usable items, see DD-34)",
    )
    parser.add_argument(
        "--write-ledger",
        default=None,
        help="Append this tool call to a ledger JSON path",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    request = {
        "home_team": args.home,
        "away_team": args.away,
        "kickoff": args.kickoff,
        "round_number": args.round_number,
        "venue": args.venue,
        "force_refresh": args.force_refresh,
        "max_age_days": args.max_age_days,
        "include_reddit": args.reddit,
    }
    started = datetime.now(timezone.utc)
    error = None
    response = None
    try:
        response = research_fixture(
            args.home,
            args.away,
            args.kickoff,
            round_number=args.round_number,
            venue=args.venue,
            force_refresh=args.force_refresh,
            max_age_days=args.max_age_days,
            include_reddit=args.reddit,
        )
    except Exception as e:
        error = str(e)
        logging.exception("Research failed")
        finished = datetime.now(timezone.utc)
        if args.write_ledger:
            append_tool_record(
                args.write_ledger,
                make_tool_call_record(
                    tool_name=TOOL_NAME,
                    request=request,
                    response=None,
                    started_at=started,
                    finished_at=finished,
                    error=error,
                ),
            )
        return 1

    finished = datetime.now(timezone.utc)
    if args.write_ledger:
        append_tool_record(
            args.write_ledger,
            make_tool_call_record(
                tool_name=TOOL_NAME,
                request=request,
                response=response,
                started_at=started,
                finished_at=finished,
            ),
        )

    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
