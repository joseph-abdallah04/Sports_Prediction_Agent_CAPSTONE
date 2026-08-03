"""In-process fact-tool bridge (same entrypoints as MCP gateway tools)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_TOOLS = Path(__file__).resolve().parents[3] / "tools"
for _name in ("mathematical_engine", "fixture_scene", "qualitative_research"):
    _p = str(_TOOLS / _name)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from feature_engineering.inference import FixtureError  # noqa: E402
from model.serving import ModelNotTrainedError, predict_fixture  # noqa: E402
from research.assemble import research_fixture  # noqa: E402
from scene.assemble import research_scene  # noqa: E402
from scene.draw import FixtureNotFoundError  # noqa: E402


def set_fixture_scene(
    home_team: str,
    away_team: str,
    *,
    season: int | None = None,
    round_number: int | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    try:
        return research_scene(
            home_team,
            away_team,
            season=season,
            round_number=round_number,
            force_refresh=force_refresh,
        )
    except FixtureNotFoundError as e:
        return {"error": "fixture_not_found", "detail": str(e)}
    except Exception as e:
        return {"error": "scene_failed", "detail": str(e)}


def research_fixture_news(
    home_team: str,
    away_team: str,
    kickoff: str,
    *,
    round_number: int | None = None,
    venue: str | None = None,
    force_refresh: bool = False,
    max_age_days: int = 10,
    queries: list[str] | None = None,
) -> dict[str, Any]:
    try:
        return research_fixture(
            home_team,
            away_team,
            kickoff,
            round_number=round_number,
            venue=venue,
            force_refresh=force_refresh,
            max_age_days=max_age_days,
            queries=queries,
        )
    except Exception as e:
        return {"error": "research_failed", "detail": str(e)}


def predict_match(
    home_team: str,
    away_team: str,
    venue: str,
    kickoff: str,
    *,
    weather: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    try:
        return predict_fixture(
            home_team=home_team,
            away_team=away_team,
            venue=venue,
            kickoff=kickoff,
            weather=weather,
            top_k=top_k,
        )
    except ModelNotTrainedError as e:
        return {"error": "model_not_trained", "detail": str(e)}
    except FixtureError as e:
        return {"error": "fixture_error", "detail": str(e)}
    except Exception as e:
        return {"error": "predict_failed", "detail": str(e)}
