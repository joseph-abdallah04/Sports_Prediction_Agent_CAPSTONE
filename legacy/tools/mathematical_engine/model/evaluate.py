"""Honest backtest on the untouched 2025-2026 holdout.

Unlike train.py (which fits the served model on all data), this trains the
base model on development data only (<=2024) and evaluates on the 2025-2026
holdout the tuner never saw - the closest thing to "how will this do on
next season". It also:
  - compares sigmoid vs isotonic calibration on the holdout,
  - draws a reliability (calibration) curve,
  - computes global SHAP feature importance,
and writes plots + metrics to reports/ for the capstone write-up.

Usage:
    uv run python -m model.evaluate
"""

import json
import logging
import os
import sys
import tempfile

# Use a guaranteed-writable matplotlib cache dir (avoids HOME-not-writable issues).
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shap
from sklearn.calibration import calibration_curve
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from xgboost import XGBClassifier

from . import (
    ENGINE_ROOT,
    development_split,
    expanding_window_folds,
    get_feature_columns,
    load_dataset,
)
from .calibration import ProbabilityCalibrator
from .train import load_params

logger = logging.getLogger("evaluate")

LABEL_COLUMN = "home_win"
REPORTS_DIR = ENGINE_ROOT / "reports"


def fit_calibrator_on_dev_oof(dev, feature_cols, params, method):
    oof_proba, oof_y = [], []
    for _, train_idx, val_idx in expanding_window_folds(dev):
        m = XGBClassifier(**params)
        m.fit(dev.loc[train_idx, feature_cols], dev.loc[train_idx, LABEL_COLUMN])
        oof_proba.append(m.predict_proba(dev.loc[val_idx, feature_cols])[:, 1])
        oof_y.append(dev.loc[val_idx, LABEL_COLUMN].to_numpy())
    return ProbabilityCalibrator(method).fit(
        np.concatenate(oof_proba), np.concatenate(oof_y)
    )


def metrics_for(y, proba) -> dict:
    pred = (proba >= 0.5).astype(int)
    return {
        "log_loss": float(log_loss(y, proba, labels=[0, 1])),
        "brier": float(brier_score_loss(y, proba)),
        "auc": float(roc_auc_score(y, proba)),
        "accuracy": float(accuracy_score(y, pred)),
    }


def plot_calibration(y, curves: dict, path) -> None:
    plt.figure(figsize=(6, 6))
    plt.plot([0, 1], [0, 1], "k--", label="perfectly calibrated")
    for label, proba in curves.items():
        frac_pos, mean_pred = calibration_curve(y, proba, n_bins=10, strategy="quantile")
        plt.plot(mean_pred, frac_pos, marker="o", label=label)
    plt.xlabel("Mean predicted probability (home win)")
    plt.ylabel("Observed fraction of home wins")
    plt.title("Reliability diagram - 2025-2026 holdout")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def plot_shap(shap_values, X, path) -> None:
    plt.figure()
    shap.summary_plot(shap_values, X, plot_type="bar", show=False, max_display=20)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    feature_cols = get_feature_columns(df)
    params = load_params()
    dev, holdout = development_split(df)
    logger.info("Development: %d matches (<=2024), Holdout: %d matches (2025-2026)",
                len(dev), len(holdout))

    # Base model trained on development data only.
    base = XGBClassifier(**params)
    base.fit(dev[feature_cols], dev[LABEL_COLUMN])
    raw_proba = base.predict_proba(holdout[feature_cols])[:, 1]
    y = holdout[LABEL_COLUMN].to_numpy()

    # Calibrators fit on development OOF, applied to holdout.
    sigmoid = fit_calibrator_on_dev_oof(dev, feature_cols, params, "sigmoid")
    isotonic = fit_calibrator_on_dev_oof(dev, feature_cols, params, "isotonic")
    sig_proba = sigmoid.transform(raw_proba)
    iso_proba = isotonic.transform(raw_proba)

    results = {
        "uncalibrated": metrics_for(y, raw_proba),
        "sigmoid": metrics_for(y, sig_proba),
        "isotonic": metrics_for(y, iso_proba),
    }

    home_baseline_acc = float(max(y.mean(), 1 - y.mean()))
    base_rate = dev[LABEL_COLUMN].mean()
    baseline_logloss = float(log_loss(y, np.full_like(y, base_rate, dtype=float), labels=[0, 1]))

    print("\n=== Holdout (2025-2026) metrics ===")
    print(f"{'variant':<14} {'log_loss':>9} {'brier':>8} {'auc':>7} {'accuracy':>9}")
    for variant, m in results.items():
        print(f"{variant:<14} {m['log_loss']:>9.4f} {m['brier']:>8.4f} "
              f"{m['auc']:>7.4f} {m['accuracy']:>9.4f}")
    print(f"\nBaselines: always-home accuracy {home_baseline_acc:.4f}, "
          f"base-rate log loss {baseline_logloss:.4f}")
    better = "isotonic" if results["isotonic"]["brier"] < results["sigmoid"]["brier"] else "sigmoid"
    print(f"Lower Brier (better calibrated) on holdout: {better}")

    plot_calibration(y, {"sigmoid": sig_proba, "isotonic": iso_proba},
                     REPORTS_DIR / "calibration_curve.png")
    logger.info("Wrote calibration curve to reports/calibration_curve.png")

    # Global SHAP on the holdout using the dev-trained model.
    explainer = shap.TreeExplainer(base)
    shap_values = explainer.shap_values(holdout[feature_cols])
    plot_shap(shap_values, holdout[feature_cols], REPORTS_DIR / "shap_summary.png")
    mean_abs = np.abs(shap_values).mean(axis=0)
    order = np.argsort(mean_abs)[::-1]
    print("\n=== Top 15 features by global SHAP (mean |impact|) ===")
    for i in order[:15]:
        print(f"  {feature_cols[i]:<42} {mean_abs[i]:.4f}")
    logger.info("Wrote SHAP summary to reports/shap_summary.png")

    report = {
        "holdout_metrics": results,
        "baselines": {
            "always_home_accuracy": home_baseline_acc,
            "base_rate_log_loss": baseline_logloss,
        },
        "better_calibration_on_holdout": better,
        "global_shap_top": {feature_cols[i]: float(mean_abs[i]) for i in order[:15]},
    }
    with open(REPORTS_DIR / "holdout_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info("Wrote reports/holdout_metrics.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
