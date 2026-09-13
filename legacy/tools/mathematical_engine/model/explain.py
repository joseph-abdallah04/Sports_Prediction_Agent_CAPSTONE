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
    "ctx_short_turnaround_home": ("Home on a short turnaround", lambda v: "yes" if v else "no"),
    "ctx_short_turnaround_away": ("Away on a short turnaround", lambda v: "yes" if v else "no"),
    "ctx_short_turnaround_diff": (
        "Short-turnaround imbalance",
        lambda v: "home only" if v > 0 else ("away only" if v < 0 else "neither"),
    ),
    "ctx_travel_km_home": ("Home travel to venue", lambda v: f"{v:,.0f} km"),
    "ctx_travel_km_away": ("Away travel to venue", lambda v: f"{v:,.0f} km"),
    "ctx_travel_km_diff": ("Travel-distance advantage", lambda v: f"{-v:+,.0f} km for away"),
    "ctx_weather": ("Match-day weather", lambda v: str(v)),
    "ladder_win_pct_diff": ("Season win-rate advantage", lambda v: f"{v:+.0%}"),
    "ladder_pts_per_game_diff": (
        "Ladder points differential per game",
        lambda v: f"{v:+.1f} points",
    ),
    "ladder_pos_diff": ("Ladder position advantage", lambda v: f"{v:+.0f} places"),
    "h2h5_win_rate": ("Head-to-head record (last 5)", lambda v: f"{v:.0%} to the home side"),
    "h2h5_margin_avg": ("Head-to-head average margin (last 5)", lambda v: f"{v:+.1f} points"),
    "h2h5_games": ("Head-to-head meetings on record", lambda v: f"{v:.0f} of last 5"),
}

_FAMILY_HINTS = {
    "form3_": "3-game form",
    "form5_": "5-game form",
    "mom5_": "5-game momentum",
    "wl5_": "5-game workload",
}

# Which side a feature's RAW VALUE favours, read on its own without the model:
# +1 means a higher value is better for the home side, -1 means better for away.
# Every entry is a home-minus-away differential, so the sign reads directly.
#
# A feature is listed only when its value has a baseline-free reading. Absolute
# magnitudes (ctx_travel_km_away), categoricals (ctx_weather), counts
# (h2h5_games) and workload concentration (wl5_*) mean nothing without knowing
# the league average, so they are omitted and never reported as conflicting.
_VALUE_POLARITY = {
    "elo_diff": 1,
    "pythag10_diff": 1,
    "bt_diff": 1,
    "ctx_rest_days_diff": 1,
    "ctx_travel_km_diff": -1,  # further for the home side is worse for them
    "ladder_win_pct_diff": 1,
    "ladder_pts_per_game_diff": 1,
    "ladder_pos_diff": 1,  # built as away-minus-home, so positive favours home
    "h2h5_margin_avg": 1,
    "mom5_last20_net_points_diff": 1,
    "mom5_first_to_score_rate_diff": 1,
    "mom5_penalty_cluster_rate_diff": -1,
}
# Rate features that pivot around a midpoint rather than zero.
_VALUE_PIVOTS = {"h2h5_win_rate": 0.5}
# Per-stat polarity for the form3_/form5_ families, keyed by the stat name.
_FORM_STAT_POLARITY = {
    "post_contact_metres": 1,
    "kicking_metres": 1,
    "play_the_ball_speed": 1,
    "possession_pct": 1,
    "completion_rate": 1,
    "effective_tackle_pct": 1,
    "line_breaks": 1,
    "tackle_breaks": 1,
    "offloads": 1,
    "all_run_metres": 1,
    "forced_drop_outs": 1,
    "support_plays": 1,
    "points_for": 1,
    "missed_tackles": -1,
    "errors": -1,
    "penalties_conceded": -1,
    "points_against": -1,
}


def _value_polarity(feature: str) -> int | None:
    """+1 if a higher raw value favours home, -1 if away, None if unreadable."""
    if feature in _VALUE_POLARITY:
        return _VALUE_POLARITY[feature]
    for family in ("form3_", "form5_"):
        if feature.startswith(family) and feature.endswith("_diff"):
            stat = feature[len(family):-len("_diff")]
            return _FORM_STAT_POLARITY.get(stat)
    return None


def _value_favours(feature: str, value) -> str | None:
    """Which club the raw value points to, ignoring the model. None if unclear."""
    if pd.isna(value) or not isinstance(value, (int, float, np.floating)):
        return None
    if feature in _VALUE_PIVOTS:
        centred = float(value) - _VALUE_PIVOTS[feature]
    else:
        polarity = _value_polarity(feature)
        if polarity is None:
            return None
        centred = float(value) * polarity
    if centred == 0:
        return None
    return "home" if centred > 0 else "away"


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


def _driver_line(feature: str, shap_value: float, value, total_abs: float) -> str:
    """Driver text carrying its weight, and a warning when the value disagrees.

    Grouping is by SHAP sign but the number shown is the raw feature value, and
    a tree model can push toward home on a value that plainly favours away
    (interactions, or credit split across correlated features). Without the
    share, five-a-side lists also read as an even contest when one side's
    attribution dwarfs the other's. Both are stated so neither can mislead.
    """
    line = _describe_driver(feature, value)
    share = abs(shap_value) / total_abs if total_abs else 0.0
    line += f" — contribution {abs(shap_value):.3f} ({share:.0%} of total)"

    favours = _value_favours(feature, value)
    contribution_side = "home" if shap_value > 0 else "away"
    if favours is not None and favours != contribution_side:
        line += (
            f"; CONFLICT: the raw value on its own favours the {favours} side — "
            f"the model still nets it toward {contribution_side} here"
        )
    return line


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

    total_abs = float(np.abs(shap_values).sum())
    toward_home = float(shap_values[shap_values > 0].sum())
    toward_away = float(-shap_values[shap_values < 0].sum())

    # Only over the drivers actually published below: naming a conflict on a
    # feature the judge never sees invites it to cite a driver that is not in
    # either group, which the verifier then reads as fabrication.
    shown = [(f, s, v) for f, s, v in positive if s > 0]
    shown += [(f, s, v) for f, s, v in negative if s < 0]
    conflicts = [
        _describe_driver(f, v)
        for f, s, v in shown
        if (fav := _value_favours(f, v)) is not None
        and fav != ("home" if s > 0 else "away")
    ]

    return {
        "prediction": prediction,
        "probability": round(confidence, 4),
        "home_win_probability": round(home_proba, 4),
        "shap_explanations": {
            "positive_drivers": [
                _driver_line(f, s, v, total_abs) for f, s, v in positive if s > 0
            ],
            "negative_drivers": [
                _driver_line(f, s, v, total_abs) for f, s, v in negative if s < 0
            ],
            # Across all features, not just the top_k shown, so the judge can see
            # when one side's list is cosmetically equal but far lighter.
            "attribution_balance": {
                "total_toward_home": round(toward_home, 4),
                "total_toward_away": round(toward_away, 4),
                "net": round(toward_home - toward_away, 4),
                "leans": (
                    "home" if toward_home > toward_away
                    else "away" if toward_away > toward_home
                    else "level"
                ),
                "note": (
                    "Summed SHAP over all features. Equal-length driver lists do "
                    "not mean equal weight; compare these totals."
                ),
            },
            "value_contribution_conflicts": conflicts,
        },
    }
