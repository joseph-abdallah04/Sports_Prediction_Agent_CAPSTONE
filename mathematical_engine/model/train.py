"""Train the production model (fast, repeatable - this is the weekly step).

Pipeline:
  1. Load tuned hyperparameters from models/best_params.json.
  2. Build out-of-time (OOF) predictions across the expanding-window folds
     and fit the probability calibrator on them - calibration is learned
     from data the base model did not train on, so it generalises.
  3. Refit the base model on ALL available matches (2015-present) so the
     served model is maximally informed.
  4. Save artifacts: model.ubj, calibrator.pkl, feature_columns.json,
     metrics.json.

This is the routine the weekly ETL (Job B) re-runs after each round; it
reuses the saved hyperparameters and takes seconds.

Usage:
    uv run python -m model.train
    uv run python -m model.train --calibration isotonic
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.metrics import brier_score_loss, log_loss
from xgboost import XGBClassifier

from . import (
    BEST_PARAMS_PATH,
    CALIBRATOR_PATH,
    FEATURE_COLUMNS_PATH,
    METRICS_PATH,
    MODEL_PATH,
    MODELS_DIR,
    development_split,
    expanding_window_folds,
    get_feature_columns,
    load_dataset,
)
from .calibration import ProbabilityCalibrator

logger = logging.getLogger("train")

LABEL_COLUMN = "home_win"
DEFAULT_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "enable_categorical": True,
    "tree_method": "hist",
    "random_state": 42,
    "n_estimators": 250,
    "max_depth": 3,
    "learning_rate": 0.03,
}


def load_params() -> dict:
    """Tuned params if present, else sensible defaults (with a warning)."""
    if BEST_PARAMS_PATH.exists():
        with open(BEST_PARAMS_PATH, encoding="utf-8") as f:
            payload = json.load(f)
        params = {**payload.get("static_params", {}), **payload.get("best_params", {})}
        logger.info("Loaded tuned hyperparameters from %s", BEST_PARAMS_PATH)
        return params
    logger.warning("No best_params.json found - using defaults. Run model.tune first.")
    return dict(DEFAULT_PARAMS)


def out_of_time_predictions(dev, feature_cols, params):
    """Concatenated validation-fold predictions the base model never trained on."""
    oof_proba, oof_y = [], []
    for val_season, train_idx, val_idx in expanding_window_folds(dev):
        model = XGBClassifier(**params)
        model.fit(dev.loc[train_idx, feature_cols], dev.loc[train_idx, LABEL_COLUMN])
        oof_proba.append(model.predict_proba(dev.loc[val_idx, feature_cols])[:, 1])
        oof_y.append(dev.loc[val_idx, LABEL_COLUMN].to_numpy())
    return np.concatenate(oof_proba), np.concatenate(oof_y)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train + calibrate the production model")
    parser.add_argument("--calibration", choices=["sigmoid", "isotonic"], default="sigmoid")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    df = load_dataset()
    feature_cols = get_feature_columns(df)
    params = load_params()
    dev, holdout = development_split(df)

    # Step 2: OOF predictions -> calibrator.
    oof_proba, oof_y = out_of_time_predictions(dev, feature_cols, params)
    calibrator = ProbabilityCalibrator(method=args.calibration).fit(oof_proba, oof_y)
    cal_proba = calibrator.transform(oof_proba)

    oof_metrics = {
        "log_loss_uncalibrated": float(log_loss(oof_y, oof_proba, labels=[0, 1])),
        "log_loss_calibrated": float(log_loss(oof_y, cal_proba, labels=[0, 1])),
        "brier_uncalibrated": float(brier_score_loss(oof_y, oof_proba)),
        "brier_calibrated": float(brier_score_loss(oof_y, cal_proba)),
    }
    logger.info(
        "OOF log loss %.4f -> %.4f, Brier %.4f -> %.4f (after %s calibration)",
        oof_metrics["log_loss_uncalibrated"], oof_metrics["log_loss_calibrated"],
        oof_metrics["brier_uncalibrated"], oof_metrics["brier_calibrated"],
        args.calibration,
    )

    # Step 3: refit base model on ALL matches (production model is maximally informed).
    model = XGBClassifier(**params)
    model.fit(df[feature_cols], df[LABEL_COLUMN])

    # Step 4: persist artifacts.
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(MODEL_PATH)
    joblib.dump({"calibrator": calibrator, "method": args.calibration}, CALIBRATOR_PATH)

    categorical = {}
    if "ctx_weather" in df.columns:
        categorical["ctx_weather"] = list(df["ctx_weather"].cat.categories)
    with open(FEATURE_COLUMNS_PATH, "w", encoding="utf-8") as f:
        json.dump({"features": feature_cols, "categorical": categorical}, f, indent=2)

    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_training_rows": int(len(df)),
        "training_seasons": [int(df["season"].min()), int(df["season"].max())],
        "calibration_method": args.calibration,
        "hyperparameters": params,
        "oof_metrics": oof_metrics,
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info("Saved model + calibrator + metadata to %s", MODELS_DIR)
    logger.info("Production model trained on %d matches (seasons %d-%d)",
                len(df), df["season"].min(), df["season"].max())
    return 0


if __name__ == "__main__":
    sys.exit(main())
