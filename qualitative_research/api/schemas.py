"""FastAPI schemas for the research tool."""

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    home_team: str = Field(..., examples=["Broncos"])
    away_team: str = Field(..., examples=["Storm"])
    kickoff: str = Field(..., examples=["2026-07-25T19:30:00+10:00"])
    round_number: int | None = Field(None, examples=[21])
    venue: str | None = None
    force_refresh: bool = False
    max_age_days: int = Field(10, ge=1, le=30)


class HealthResponse(BaseModel):
    status: str
    tool: str
    version: str
