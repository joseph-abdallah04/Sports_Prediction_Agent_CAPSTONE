"""CLI: set the scene for an upcoming NRL fixture.

Usage:
    uv run python -m scene.cli --home Eels --away Panthers
    uv run python -m scene.cli --home Eels --away Panthers --round 21 --force-refresh
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scene import TOOL_NAME
from scene.assemble import research_scene
from scene.draw import FixtureNotFoundError
from scene.ledger_types import append_tool_record, make_tool_call_record


def main() -> int:
    parser = argparse.ArgumentParser(description="NRL fixture scene setter")
    parser.add_argument("--home", required=True)
    parser.add_argument("--away", required=True)
    parser.add_argument("--season", type=int, default=None)
    parser.add_argument("--round", type=int, default=None, dest="round_number")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--write-ledger", default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    request = {
        "home_team": args.home,
        "away_team": args.away,
        "season": args.season,
        "round_number": args.round_number,
        "force_refresh": args.force_refresh,
    }
    started = datetime.now(timezone.utc)
    error = None
    response = None
    try:
        response = research_scene(
            args.home,
            args.away,
            season=args.season,
            round_number=args.round_number,
            force_refresh=args.force_refresh,
        )
    except FixtureNotFoundError as e:
        error = str(e)
        logging.error("%s", e)
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
    except Exception as e:
        error = str(e)
        logging.exception("Scene failed")
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
