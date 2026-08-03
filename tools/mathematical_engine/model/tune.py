"""Hyperparameter tuning with Optuna (run occasionally, not weekly).

Searches XGBoost hyperparameters by minimising mean log loss across the
expanding-window chronological folds (2021-2024 validation seasons). The
2025-2026 holdout is never touched here. The winning parameters are saved
to models/best_params.json for train.py to consume.

Why log loss, not accuracy: the LLM Orchestrator consumes the predicted
probability, so we optimise probability quality (proper scoring rule), not
just whether the argmax was right.

Why tune occasionally: the best hyperparameters reflect the dataset's shape
(~2,300 rows, 49 features, NRL noise), which adding one round of matches
does not change. Weekly retraining reuses these saved params; re-tune each
off-season or after significant feature changes.

Usage:
    uv run python -m model.tune                 # ~200 trials (default)
    uv run python -m model.tune --trials 50     # quicker
"""

import argparse
import json
import logging
import sys

import numpy as np
import optuna
from sklearn.metrics import log_loss
from xgboost import XGBClassifier

from . import (
    BEST_PARAMS_PATH,
    MODELS_DIR,
    development_split,
    expanding_window_folds,
    get_feature_columns,
    load_dataset,
)

logger = logging.getLogger("tune")

# Fixed across all trials; only the searched params vary.
STATIC_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "enable_categorical": True,
    "tree_method": "hist",
    "random_state": 42,
}


def build_search_space(trial: optuna.Trial) -> dict:
    return {
        "n_estimators": trial.suggest_int("n_estimators", 100, 800, step=50),
        "max_depth": trial.suggest_int("max_depth", 2, 8),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
        "gamma": trial.suggest_float("gamma", 1e-3, 5.0, log=True),
    }


def make_objective(dev, feature_cols, label_col):
    folds = list(expanding_window_folds(dev))

    def objective(trial: optuna.Trial) -> float:
        params = {**STATIC_PARAMS, **build_search_space(trial)}
        fold_losses = []
        for val_season, train_idx, val_idx in folds:
            model = XGBClassifier(**params)
            model.fit(
                dev.loc[train_idx, feature_cols],
                dev.loc[train_idx, label_col],
            )
            proba = model.predict_proba(dev.loc[val_idx, feature_cols])[:, 1]
            fold_losses.append(
                log_loss(dev.loc[val_idx, label_col], proba, labels=[0, 1])
            )
        return float(np.mean(fold_losses))

    return objective


def main() -> int:
    parser = argparse.ArgumentParser(description="Optuna hyperparameter search")
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    df = load_dataset()
    feature_cols = get_feature_columns(df)
    label_col = "home_win"
    dev, _ = development_split(df)

    folds = list(expanding_window_folds(dev))
    logger.info(
        "Tuning on %d development matches across %d expanding-window folds (val seasons %s)",
        len(dev), len(folds), [f[0] for f in folds],
    )

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=args.seed),
    )
    study.optimize(make_objective(dev, feature_cols, label_col), n_trials=args.trials)

    logger.info("Best mean log loss: %.4f", study.best_value)
    logger.info("Best params: %s", study.best_params)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "best_params": study.best_params,
        "static_params": STATIC_PARAMS,
        "best_cv_log_loss": study.best_value,
        "n_trials": args.trials,
        "val_seasons": [f[0] for f in folds],
    }
    with open(BEST_PARAMS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    logger.info("Saved best params to %s", BEST_PARAMS_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
