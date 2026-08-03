"""Stage 2 orchestrator: build the model-ready training dataset.

Loads feature_store/matches_flat.parquet (running Stage 1 first if it is
missing), computes all pre-match features chronologically, and writes
feature_store/training_dataset.parquet.

Usage:
    uv run python -m feature_engineering.build_dataset
    uv run python -m feature_engineering.build_dataset --reflatten --min-history 5
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from .context import add_context_features
from .flatten import FEATURE_STORE_DIR, OUTPUT_PATH as FLAT_PATH, build_flat_table
from .ratings import add_rating_features
from .rolling_form import build_team_perspective, add_rolling_features
from .standings import add_standings_features

logger = logging.getLogger("build_dataset")

DATASET_PATH = FEATURE_STORE_DIR / "training_dataset.parquet"

ID_COLUMNS = [
    "match_id", "season", "round_number", "start_time",
    "home_team", "away_team", "venue",
]
LABEL_COLUMN = "home_win"
RATING_FEATURES = ["elo_diff", "pythag10_diff", "bt_diff"]
CONTEXT_FEATURES = [
    "ctx_venue_hga", "ctx_rest_days_home", "ctx_rest_days_away",
    "ctx_rest_days_diff", "ctx_travel_away", "ctx_weather",
    "ctx_short_turnaround_home", "ctx_short_turnaround_away",
    "ctx_short_turnaround_diff",
    "ctx_travel_km_home", "ctx_travel_km_away", "ctx_travel_km_diff",
]
STANDINGS_FEATURES = [
    "ladder_win_pct_diff", "ladder_pts_per_game_diff", "ladder_pos_diff",
    "h2h5_win_rate", "h2h5_margin_avg", "h2h5_games",
]

# Feature groups added after the v1 model shipped. Passing --baseline-features
# rebuilds the exact v1 column set so a retrain can be compared like-for-like.
CANDIDATE_FEATURES = STANDINGS_FEATURES + [
    "ctx_short_turnaround_home", "ctx_short_turnaround_away",
    "ctx_short_turnaround_diff",
    "ctx_travel_km_home", "ctx_travel_km_away", "ctx_travel_km_diff",
]


def games_played_before(df: pd.DataFrame) -> pd.DataFrame:
    """Prior game counts per side, used for the --min-history filter."""
    long_df = build_team_perspective(df)
    long_df["prior_games"] = long_df.groupby("team_id", sort=False).cumcount()
    counts = long_df.pivot(index="match_id", columns="side", values="prior_games")
    return counts.rename(columns={"home": "home_prior_games", "away": "away_prior_games"})


def build(
    min_history: int, reflatten: bool, baseline_features: bool = False
) -> pd.DataFrame:
    if reflatten or not FLAT_PATH.exists():
        logger.info("Running Stage 1 flatten...")
        flat = build_flat_table()
        FEATURE_STORE_DIR.mkdir(parents=True, exist_ok=True)
        flat.to_parquet(FLAT_PATH, index=False)
    else:
        flat = pd.read_parquet(FLAT_PATH)

    flat = flat.sort_values("start_time").reset_index(drop=True)

    df = add_rating_features(flat)
    df = add_context_features(df)
    df = add_standings_features(df)
    df = add_rolling_features(df)

    rolling_features = [c for c in df.columns if c.endswith("_diff") and (
        c.startswith(("form3_", "form5_", "mom5_", "wl5_"))
    )]
    feature_columns = (
        RATING_FEATURES + CONTEXT_FEATURES + STANDINGS_FEATURES + rolling_features
    )
    if baseline_features:
        feature_columns = [c for c in feature_columns if c not in CANDIDATE_FEATURES]
        logger.info("Baseline feature set: %d columns", len(feature_columns))

    dataset = df[ID_COLUMNS + [LABEL_COLUMN] + feature_columns].copy()

    if min_history > 0:
        counts = games_played_before(flat)
        dataset = dataset.join(counts, on="match_id")
        before = len(dataset)
        dataset = dataset[
            (dataset["home_prior_games"] >= min_history)
            & (dataset["away_prior_games"] >= min_history)
        ].drop(columns=["home_prior_games", "away_prior_games"])
        logger.info("min-history=%d filter dropped %d rows", min_history, before - len(dataset))

    return dataset


def print_coverage(dataset: pd.DataFrame) -> None:
    feature_cols = [c for c in dataset.columns if c not in ID_COLUMNS + [LABEL_COLUMN]]
    null_rates = dataset.groupby("season")[feature_cols].apply(lambda g: g.isna().mean())
    worst = null_rates.max().sort_values(ascending=False)
    print("\n=== Feature coverage (worst per-season null rate per feature) ===")
    for feature, rate in worst.items():
        if rate > 0:
            seasons = null_rates.index[null_rates[feature] > 0].tolist()
            print(f"  {feature:<42} max {rate:>5.0%}  (seasons: {seasons})")
    fully_covered = (worst == 0).sum()
    print(f"  ...and {fully_covered} features with zero nulls in every season")
    print(f"\nRows: {len(dataset)}, features: {len(feature_cols)}, "
          f"home-win rate: {dataset['home_win'].mean():.3f}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the training dataset (Stage 2)")
    parser.add_argument("--reflatten", action="store_true", help="re-run Stage 1 first")
    parser.add_argument("--min-history", type=int, default=0,
                        help="drop rows where either team has fewer prior games")
    parser.add_argument("--baseline-features", action="store_true",
                        help="exclude post-v1 candidate features (for A/B retrains)")
    parser.add_argument("--out", type=str, default=None,
                        help="output parquet path (default: training_dataset.parquet)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    dataset = build(args.min_history, args.reflatten, args.baseline_features)
    FEATURE_STORE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else DATASET_PATH
    dataset.to_parquet(out_path, index=False)
    logger.info("Wrote %d rows x %d cols to %s", len(dataset), dataset.shape[1], out_path)
    print_coverage(dataset)
    return 0


if __name__ == "__main__":
    sys.exit(main())
