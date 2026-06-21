"""SHAP-based reasoning payload for a single prediction.

Converts a model prediction into the contextualised JSON the LLM
Orchestrator consumes (see mathematical_engine/Overview.md): the predicted
outcome, its calibrated probability, and the feature drivers that pushed the
prediction toward each side - in human-readable language.

SHAP attributes the model's raw log-odds output across features. Because
calibration is a monotonic transform, it changes the probability scale but
not which features drove the decision or in what direction, so we explain
the raw margin and report the calibrated probability.
"""

import numpy as np
import pandas as pd
import shap

# Human-readable phrasing per feature. Each entry: (label, value formatter).
# Anything not listed falls back to a prettified name + signed value.
_DRIVER_LABELS = {
    "elo_diff": ("Elo rating advantage", lambda v: f"{v:+.0f} points"),
    "bt_diff": ("Bradley-Terry strength advantage", lambda v: f"{v:+.2f} log-strength"),
    "pythag10_diff": ("Pythagorean form (last 10)", lambda v: f"{v:+.0%} expected-win gap"),
    "ctx_venue_hga": ("Venue home advantage", lambda v: f"{v:.0%} historical home rate"),
    "ctx_rest_days_diff": ("Rest-day advantage", lambda v: f"{v:+.1f} days"),
    "ctx_rest_days_home": ("Home rest", lambda v: f"{v:.1f} days"),
    "ctx_rest_days_away": ("Away rest", lambda v: f"{v:.1f} days"),
    "ctx_travel_away": ("Away interstate travel", lambda v: "yes" if v else "no"),
}

_FAMILY_HINTS = {
    "form3_": "3-game form",
    "form5_": "5-game form",
    "mom5_": "5-game momentum",
    "wl5_": "5-game workload",
}


def _pretty_name(feature: str) -> str:
    prefix = ""
    for fam, hint in _FAMILY_HINTS.items():
        if feature.startswith(fam):
            prefix = f"{hint}: "
            feature = feature[len(fam):]
            break
    name = feature.replace("_diff", "").replace("_", " ").strip()
    return prefix + name


def _describe_driver(feature: str, value) -> str:
    if pd.isna(value):
        detail = "no data"
    elif feature in _DRIVER_LABELS:
        label, fmt = _DRIVER_LABELS[feature]
        return f"{label} ({fmt(value)})"
    else:
        detail = f"{value:+.2f}" if isinstance(value, (int, float, np.floating)) else str(value)
    return f"{_pretty_name(feature)} ({detail})"


def explain_prediction(
    model,
    calibrator,
    feature_row: pd.Series,
    feature_cols: list[str],
    categoricals: dict[str, list] | None = None,
    top_k: int = 5,
) -> dict:
    """Build the Overview-format reasoning payload for one fixture.

    Args:
        model: fitted XGBClassifier.
        calibrator: fitted ProbabilityCalibrator (or None).
        feature_row: the fixture's feature vector (indexed by feature name).
        feature_cols: ordered feature names the model expects.
        categoricals: {column: category list} to rebuild the exact category
            dtype the model trained with (required for XGBoost categoricals).
        top_k: number of drivers to report per direction.
    """
    categoricals = categoricals or {}
    X = feature_row[feature_cols].to_frame().T
    for col in feature_cols:
        if col in categoricals:
            X[col] = pd.Categorical(X[col], categories=categoricals[col])
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce")

    raw_proba = float(model.predict_proba(X)[:, 1][0])
    home_proba = float(calibrator.transform([raw_proba])[0]) if calibrator else raw_proba

    prediction = "Home Win" if home_proba >= 0.5 else "Away Win"
    confidence = home_proba if home_proba >= 0.5 else 1 - home_proba

    explainer = shap.TreeExplainer(model)
    shap_values = np.asarray(explainer.shap_values(X)).reshape(-1)

    contributions = sorted(
        zip(feature_cols, shap_values, (feature_row[c] for c in feature_cols)),
        key=lambda t: t[1],
    )
    # Positive SHAP pushes toward home win, negative toward away win.
    negative = contributions[:top_k]  # most pro-away
    positive = contributions[-top_k:][::-1]  # most pro-home

    return {
        "prediction": prediction,
        "probability": round(confidence, 4),
        "home_win_probability": round(home_proba, 4),
        "shap_explanations": {
            "positive_drivers": [
                _describe_driver(f, v) for f, s, v in positive if s > 0
            ],
            "negative_drivers": [
                _describe_driver(f, v) for f, s, v in negative if s < 0
            ],
        },
    }
