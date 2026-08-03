"""A/B a candidate feature group against the shipped baseline feature set.

New features are only worth shipping if they buy real out-of-time accuracy.
This script trains the same architecture twice - once on the baseline columns
the production model already uses, once with the candidate columns added -
and scores both on the untouched holdout seasons.

Both arms use identical hyperparameters, identical splits, and the same set of
random seeds, so the only thing that varies is the feature set. Results are
averaged across seeds because a single XGBoost fit on ~2.4k rows moves by
roughly +/-0.01 AUC on seed alone, which is the same order as the effect being
measured.

Usage:
    uv run python -m model.feature_ab
    uv run python -m model.feature_ab --seeds 10
"""

import argparse
import json
import logging
import sys

import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from xgboost import XGBClassifier

from feature_engineering.build_dataset import CANDIDATE_FEATURES

from . import development_split, get_feature_columns, load_dataset
from .train import load_params

logger = logging.getLogger("feature_ab")

LABEL_COLUMN = "home_win"


def evaluate_feature_set(dev, holdout, feature_cols, params, seeds) -> dict:
    """Mean holdout metrics across seeds for one feature set."""
    y = holdout[LABEL_COLUMN].to_numpy()
    runs = []
    for seed in seeds:
        model = XGBClassifier(**{**params, "random_state": seed})
        model.fit(dev[feature_cols], dev[LABEL_COLUMN])
        proba = model.predict_proba(holdout[feature_cols])[:, 1]
        runs.append(
            {
                "log_loss": float(log_loss(y, proba, labels=[0, 1])),
                "brier": float(brier_score_loss(y, proba)),
                "auc": float(roc_auc_score(y, proba)),
                "accuracy": float(accuracy_score(y, (proba >= 0.5).astype(int))),
            }
        )
    summary = {k: float(np.mean([r[k] for r in runs])) for k in runs[0]}
    summary["auc_std"] = float(np.std([r["auc"] for r in runs]))
    summary["n_features"] = len(feature_cols)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="A/B candidate features on the holdout")
    parser.add_argument("--seeds", type=int, default=8, help="number of random seeds")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    df = load_dataset()
    all_features = get_feature_columns(df)
    candidate_present = [c for c in CANDIDATE_FEATURES if c in all_features]
    if not candidate_present:
        logger.error(
            "No candidate features in the dataset. Rebuild it with "
            "feature_engineering.build_dataset first."
        )
        return 1
    baseline_features = [c for c in all_features if c not in candidate_present]

    params = load_params()
    dev, holdout = development_split(df)
    seeds = list(range(args.seeds))
    logger.info(
        "Dev %d matches (<=2024), holdout %d matches (2025-2026), %d seeds",
        len(dev), len(holdout), len(seeds),
    )

    results = {
        "baseline": evaluate_feature_set(dev, holdout, baseline_features, params, seeds),
        "candidate": evaluate_feature_set(dev, holdout, all_features, params, seeds),
    }

    print("\n=== Holdout, averaged over "
          f"{len(seeds)} seeds ===")
    print(f"{'arm':<12} {'features':>9} {'log_loss':>9} {'brier':>8} "
          f"{'auc':>7} {'auc_sd':>7} {'accuracy':>9}")
    for arm, m in results.items():
        print(f"{arm:<12} {m['n_features']:>9} {m['log_loss']:>9.4f} {m['brier']:>8.4f} "
              f"{m['auc']:>7.4f} {m['auc_std']:>7.4f} {m['accuracy']:>9.4f}")

    delta_auc = results["candidate"]["auc"] - results["baseline"]["auc"]
    delta_ll = results["candidate"]["log_loss"] - results["baseline"]["log_loss"]
    print(f"\nCandidate adds: {', '.join(candidate_present)}")
    print(f"Delta AUC {delta_auc:+.4f}, delta log loss {delta_ll:+.4f} "
          f"(log loss: lower is better)")
    verdict = "SHIP" if delta_auc > 0 and delta_ll < 0 else "DO NOT SHIP"
    print(f"Verdict: {verdict}")

    print(json.dumps({"delta_auc": delta_auc, "delta_log_loss": delta_ll}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
