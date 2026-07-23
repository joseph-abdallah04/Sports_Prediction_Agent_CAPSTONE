"""API routes for qualitative research."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from research import TOOL_NAME, TOOL_VERSION
from research.assemble import research_fixture

from .schemas import HealthResponse, ResearchRequest

logger = logging.getLogger("api")
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", tool=TOOL_NAME, version=TOOL_VERSION)


@router.post("/research", tags=["research"])
def research(request: ResearchRequest) -> dict:
    """Gather qualitative facts for an upcoming fixture (no LLM analysis)."""
    try:
        return research_fixture(
            request.home_team,
            request.away_team,
            request.kickoff,
            round_number=request.round_number,
            venue=request.venue,
            force_refresh=request.force_refresh,
            max_age_days=request.max_age_days,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Research failed")
        raise HTTPException(status_code=500, detail=str(e))
