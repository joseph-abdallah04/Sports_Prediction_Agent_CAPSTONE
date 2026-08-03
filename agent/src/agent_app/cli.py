"""CLI for the NRL prediction agent.

Usage:
    cd agent && uv sync
    uv run python -m agent_app.cli --home Eels --away Panthers
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure src layout imports work when run as module
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from agent_app.config import get_settings
from agent_app.orchestrator import run_prediction


def main() -> int:
    parser = argparse.ArgumentParser(description="NRL Capstone prediction agent")
    parser.add_argument("--home", required=True)
    parser.add_argument("--away", required=True)
    parser.add_argument("--question", default=None, help="Optional user question")
    parser.add_argument("--season", type=int, default=None)
    parser.add_argument("--round", type=int, default=None, dest="round_number")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Keep default terminal readable: stage banners stay INFO; quiet chatty libs.
    if not args.verbose:
        for noisy in (
            "LiteLLM",
            "litellm",
            "httpx",
            "httpcore",
            "openai",
            "primp",
            "urllib3",
            "asyncio",
        ):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    settings = get_settings()
    result = run_prediction(
        args.home,
        args.away,
        user_question=args.question,
        season=args.season,
        round_number=args.round_number,
        force_refresh=args.force_refresh,
        settings=settings,
    )
    print(json.dumps(result, indent=2, default=str))
    return 1 if result.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
