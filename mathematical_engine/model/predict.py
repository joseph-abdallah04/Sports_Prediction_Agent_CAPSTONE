"""CLI: predict an upcoming NRL fixture.

Ties the pieces together: builds the fixture's pre-match features via the
inference path (same code as training), loads the trained + calibrated
model, and prints the Overview-format reasoning payload.

Usage:
    uv run python -m model.predict --home Broncos --away Storm \
        --venue "Suncorp Stadium" --date 2026-06-20T09:30:00Z
    uv run python -m model.predict --home Sharks --away Eels \
        --venue "PointsBet Stadium" --date 2026-07-04 --weather Rain
"""

import argparse
import json
import sys

import joblib
from xgboost import XGBClassifier

from feature_engineering.inference import build_fixture_features
from . import CALIBRATOR_PATH, FEATURE_COLUMNS_PATH, MODEL_PATH
from .explain import explain_prediction


def load_artifacts():
    if not MODEL_PATH.exists():
        raise SystemExit("No trained model found. Run `uv run python -m model.train` first.")
    model = XGBClassifier(enable_categorical=True)
    model.load_model(MODEL_PATH)
    calibrator_blob = joblib.load(CALIBRATOR_PATH) if CALIBRATOR_PATH.exists() else None
    calibrator = calibrator_blob["calibrator"] if calibrator_blob else None
    with open(FEATURE_COLUMNS_PATH, encoding="utf-8") as f:
        cols_meta = json.load(f)
    return model, calibrator, cols_meta["features"], cols_meta.get("categorical", {})


def main() -> int:
    parser = argparse.ArgumentParser(description="Predict an upcoming NRL fixture")
    parser.add_argument("--home", required=True, help="home team nickname, e.g. Broncos")
    parser.add_argument("--away", required=True, help="away team nickname, e.g. Storm")
    parser.add_argument("--venue", required=True, help='venue name, e.g. "Suncorp Stadium"')
    parser.add_argument("--date", required=True, help="kickoff date/datetime (ISO, e.g. 2026-06-20)")
    parser.add_argument("--weather", default=None, help="optional: Fine, Rain, ...")
    parser.add_argument("--top-k", type=int, default=5, help="drivers per direction")
    args = parser.parse_args()

    model, calibrator, feature_cols, categoricals = load_artifacts()

    feature_row = build_fixture_features(
        home_team=args.home,
        away_team=args.away,
        venue=args.venue,
        kickoff=args.date,
        weather=args.weather,
    )

    payload = explain_prediction(
        model, calibrator, feature_row, feature_cols,
        categoricals=categoricals, top_k=args.top_k,
    )
    payload["fixture"] = {
        "home_team": args.home,
        "away_team": args.away,
        "venue": args.venue,
        "kickoff": args.date,
        "weather": args.weather or "unknown",
    }

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
