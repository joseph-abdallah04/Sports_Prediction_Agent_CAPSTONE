"""API routes: POST /predict and GET /health."""

import logging

from fastapi import APIRouter, HTTPException

from feature_engineering.inference import FixtureError
from model.serving import ModelNotTrainedError, get_bundle, predict_fixture

from .schemas import ErrorResponse, HealthResponse, PredictRequest, PredictResponse

logger = logging.getLogger("api")

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    """Liveness check + which model the server would serve right now.

    Run this after a weekly ETL to confirm `trained_at` moved forward.
    """
    try:
        bundle = get_bundle()
    except ModelNotTrainedError:
        return HealthResponse(status="degraded", model_loaded=False)

    metrics = bundle.metrics
    return HealthResponse(
        status="ok",
        model_loaded=True,
        trained_at=metrics.get("trained_at"),
        n_training_rows=metrics.get("n_training_rows"),
        training_seasons=metrics.get("training_seasons"),
        calibration_method=metrics.get("calibration_method"),
    )


@router.post(
    "/predict",
    response_model=PredictResponse,
    tags=["prediction"],
    responses={
        404: {"model": ErrorResponse, "description": "No trained model available"},
        422: {"model": ErrorResponse, "description": "Unknown team/venue or invalid input"},
        503: {"model": ErrorResponse, "description": "Feature store missing - run the weekly ETL"},
    },
)
def predict(request: PredictRequest) -> dict:
    """Predict an upcoming NRL fixture.

    Builds the fixture's 49 pre-match features from all completed matches
    before kickoff, runs the calibrated XGBoost model, and returns the
    prediction with SHAP-based reasoning (the Overview hand-off contract).
    """
    try:
        return predict_fixture(
            home_team=request.home_team,
            away_team=request.away_team,
            venue=request.venue,
            kickoff=request.kickoff,
            weather=request.weather,
            top_k=request.top_k,
        )
    except ModelNotTrainedError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FixtureError as e:
        # Missing feature store is an ops problem (503); unknown team is a client problem (422).
        detail = str(e)
        status = 503 if "not found" in detail and "parquet" in detail else 422
        raise HTTPException(status_code=status, detail=detail)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid input: {e}")
