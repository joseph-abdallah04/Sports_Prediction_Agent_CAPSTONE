"""Pydantic request/response models for the prediction API.

The response mirrors the Overview.md hand-off contract exactly - the same
JSON `model.predict` prints - so the LLM Orchestrator sees one stable shape
whether the engine is called via CLI or HTTP.
"""

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """A single upcoming fixture to predict."""

    home_team: str = Field(..., description="Home team nickname, e.g. 'Broncos'", examples=["Broncos"])
    away_team: str = Field(..., description="Away team nickname, e.g. 'Storm'", examples=["Storm"])
    venue: str = Field(..., description="Venue name, e.g. 'Suncorp Stadium'", examples=["Suncorp Stadium"])
    kickoff: str = Field(
        ...,
        description="Kickoff date/datetime in ISO 8601, e.g. '2026-07-04T09:30:00Z'",
        examples=["2026-07-04T09:30:00Z"],
    )
    weather: str | None = Field(
        None, description="Optional forecast: 'Fine', 'Rain', ... Omitted = unknown"
    )
    top_k: int = Field(5, ge=1, le=20, description="SHAP drivers to return per direction")


class ShapExplanations(BaseModel):
    positive_drivers: list[str] = Field(..., description="Factors pushing toward a HOME win")
    negative_drivers: list[str] = Field(..., description="Factors pushing toward an AWAY win")


class FixtureEcho(BaseModel):
    home_team: str
    away_team: str
    venue: str
    kickoff: str
    weather: str


class PredictResponse(BaseModel):
    """Overview-format prediction payload."""

    prediction: str = Field(..., description="'Home Win' or 'Away Win'")
    probability: float = Field(..., description="Calibrated probability of the predicted outcome")
    home_win_probability: float = Field(..., description="Calibrated probability of a home win")
    shap_explanations: ShapExplanations
    fixture: FixtureEcho


class HealthResponse(BaseModel):
    """Liveness + model freshness."""

    status: str
    model_loaded: bool
    trained_at: str | None = None
    n_training_rows: int | None = None
    training_seasons: list[int] | None = None
    calibration_method: str | None = None


class ErrorResponse(BaseModel):
    detail: str
