"""Shared prediction serving layer.

One code path used by BOTH the `model.predict` CLI and the MCP gateway
(`predict_match` tool), so there is no drift between how predictions are
made on the command line and via the agent tool interface.

Also implements artifact hot-reload: the weekly ETL overwrites the files in
models/ while a long-lived process (e.g. MCP server) may be running. Before
each prediction we compare the modification time of models/metrics.json
(always rewritten last by train.py) against the loaded bundle; if it changed,
we transparently reload the model, calibrator, and feature metadata.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import joblib
from xgboost import XGBClassifier

from feature_engineering.inference import build_fixture_features
from . import CALIBRATOR_PATH, FEATURE_COLUMNS_PATH, METRICS_PATH, MODEL_PATH
from .explain import explain_prediction

logger = logging.getLogger("serving")


class ModelNotTrainedError(Exception):
    """Raised when models/ has no trained artifacts yet."""


@dataclass
class ModelBundle:
    """Everything needed to serve one prediction, loaded as a unit."""

    model: XGBClassifier
    calibrator: object | None
    feature_cols: list[str]
    categoricals: dict[str, list]
    metrics: dict
    loaded_at: datetime
    metrics_mtime: float


_bundle: ModelBundle | None = None


def _load_bundle() -> ModelBundle:
    if not MODEL_PATH.exists():
        raise ModelNotTrainedError(
            f"No trained model at {MODEL_PATH}. "
            "Run `uv run python -m model.train` (or the weekly ETL) first."
        )

    model = XGBClassifier(enable_categorical=True)
    model.load_model(MODEL_PATH)

    calibrator = None
    if CALIBRATOR_PATH.exists():
        calibrator = joblib.load(CALIBRATOR_PATH)["calibrator"]

    with open(FEATURE_COLUMNS_PATH, encoding="utf-8") as f:
        cols_meta = json.load(f)

    metrics = {}
    metrics_mtime = 0.0
    if METRICS_PATH.exists():
        with open(METRICS_PATH, encoding="utf-8") as f:
            metrics = json.load(f)
        metrics_mtime = METRICS_PATH.stat().st_mtime

    bundle = ModelBundle(
        model=model,
        calibrator=calibrator,
        feature_cols=cols_meta["features"],
        categoricals=cols_meta.get("categorical", {}),
        metrics=metrics,
        loaded_at=datetime.now(timezone.utc),
        metrics_mtime=metrics_mtime,
    )
    logger.info(
        "Loaded model artifacts (trained_at=%s, %s training rows)",
        metrics.get("trained_at", "unknown"), metrics.get("n_training_rows", "?"),
    )
    return bundle


def get_bundle() -> ModelBundle:
    """Return the current artifacts, hot-reloading if the weekly ETL replaced them."""
    global _bundle
    if _bundle is None:
        _bundle = _load_bundle()
        return _bundle

    current_mtime = METRICS_PATH.stat().st_mtime if METRICS_PATH.exists() else 0.0
    if current_mtime != _bundle.metrics_mtime:
        logger.info("models/metrics.json changed on disk - reloading artifacts")
        _bundle = _load_bundle()
    return _bundle


def predict_fixture(
    home_team: str,
    away_team: str,
    venue: str,
    kickoff: str,
    weather: str | None = None,
    top_k: int = 5,
) -> dict:
    """Full prediction pipeline for one upcoming fixture.

    Builds the 49 pre-match features via the training-parity inference path,
    runs the calibrated model, and returns the Overview-format payload.

    Raises:
        ModelNotTrainedError: models/ has no artifacts.
        FixtureError: unknown team, or the feature store is missing.
    """
    bundle = get_bundle()

    feature_row = build_fixture_features(
        home_team=home_team,
        away_team=away_team,
        venue=venue,
        kickoff=kickoff,
        weather=weather,
    )

    payload = explain_prediction(
        bundle.model,
        bundle.calibrator,
        feature_row,
        bundle.feature_cols,
        categoricals=bundle.categoricals,
        top_k=top_k,
    )
    payload["fixture"] = {
        "home_team": home_team,
        "away_team": away_team,
        "venue": venue,
        "kickoff": kickoff,
        "weather": weather or "unknown",
    }
    return payload
