"""CLI: predict an upcoming NRL fixture.

Thin wrapper around model/serving.py - the same predict_fixture() the
FastAPI endpoint uses, so CLI and HTTP predictions can never diverge.

Usage:
    uv run python -m model.predict --home Broncos --away Storm \
        --venue "Suncorp Stadium" --date 2026-07-04T09:30:00Z
    uv run python -m model.predict --home Sharks --away Eels \
        --venue "PointsBet Stadium" --date 2026-07-04 --weather Rain
"""

import argparse
import json
import sys

from feature_engineering.inference import FixtureError
from .serving import ModelNotTrainedError, predict_fixture


def main() -> int:
    parser = argparse.ArgumentParser(description="Predict an upcoming NRL fixture")
    parser.add_argument("--home", required=True, help="home team nickname, e.g. Broncos")
    parser.add_argument("--away", required=True, help="away team nickname, e.g. Storm")
    parser.add_argument("--venue", required=True, help='venue name, e.g. "Suncorp Stadium"')
    parser.add_argument("--date", required=True, help="kickoff date/datetime (ISO, e.g. 2026-06-20)")
    parser.add_argument("--weather", default=None, help="optional: Fine, Rain, ...")
    parser.add_argument("--top-k", type=int, default=5, help="drivers per direction")
    args = parser.parse_args()

    try:
        payload = predict_fixture(
            home_team=args.home,
            away_team=args.away,
            venue=args.venue,
            kickoff=args.date,
            weather=args.weather,
            top_k=args.top_k,
        )
    except (ModelNotTrainedError, FixtureError) as e:
        raise SystemExit(str(e))

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
