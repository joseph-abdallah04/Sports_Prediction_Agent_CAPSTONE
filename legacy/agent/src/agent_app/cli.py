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

from agent_app.config import (
    PROVIDERS,
    describe_settings,
    get_settings,
    missing_credentials,
)
from agent_app.orchestrator import run_prediction


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NRL Capstone prediction agent",
        epilog="Defaults come from config.toml at the repo root.",
    )
    parser.add_argument("--home")
    parser.add_argument("--away")
    parser.add_argument("--question", default=None, help="Optional user question")
    parser.add_argument("--season", type=int, default=None)
    parser.add_argument("--round", type=int, default=None, dest="round_number")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument(
        "--provider",
        choices=PROVIDERS,
        default=None,
        help="Override config.toml for this run only",
    )
    parser.add_argument(
        "--model", default=None, help="Override the provider's model for this run only"
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Print the resolved configuration and exit",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    overrides: dict[str, str] = {}
    if args.provider:
        overrides["llm_provider"] = args.provider
    if args.model:
        overrides["llm_model"] = args.model

    if args.show_config:
        print(describe_settings(get_settings(**overrides)))
        return 0

    if not args.home or not args.away:
        parser.error("--home and --away are required (or use --show-config)")

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

    settings = get_settings(**overrides)
    warning = missing_credentials(settings)
    if warning:
        logging.getLogger("agent_app.cli").error("%s", warning)
        return 2

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
