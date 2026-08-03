"""Probability calibration.

A model's raw output of "0.70" should mean the home team wins ~70% of the
time. Tree ensembles are often miscalibrated, so we fit a post-hoc mapping
from raw probabilities to calibrated ones. The LLM Orchestrator reasons
with this probability directly, so calibration matters as much as ranking.

Two standard methods, compared in evaluate.py:
  - sigmoid (Platt scaling): fits a logistic curve; robust with little data.
  - isotonic: fits a free monotonic step function; more flexible, needs more
    data and can overfit small calibration sets.
"""

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

_EPS = 1e-6


class ProbabilityCalibrator:
    """Monotonic map from raw model probability to calibrated probability."""

    def __init__(self, method: str = "sigmoid"):
        if method not in ("sigmoid", "isotonic"):
            raise ValueError(f"Unknown calibration method: {method}")
        self.method = method
        self._model = None

    def fit(self, proba, y) -> "ProbabilityCalibrator":
        proba = np.clip(np.asarray(proba, dtype=float), _EPS, 1 - _EPS)
        y = np.asarray(y)
        if self.method == "sigmoid":
            logit = np.log(proba / (1 - proba)).reshape(-1, 1)
            self._model = LogisticRegression().fit(logit, y)
        else:
            self._model = IsotonicRegression(out_of_bounds="clip").fit(proba, y)
        return self

    def transform(self, proba) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Calibrator is not fitted.")
        proba = np.clip(np.asarray(proba, dtype=float), _EPS, 1 - _EPS)
        if self.method == "sigmoid":
            logit = np.log(proba / (1 - proba)).reshape(-1, 1)
            return self._model.predict_proba(logit)[:, 1]
        return self._model.predict(proba)
