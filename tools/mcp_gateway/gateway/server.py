"""NRL Capstone MCP gateway — exposes fact tools to an agent client.

Run (stdio, default for MCP hosts):
    cd tools/mcp_gateway && uv sync
    uv run python -m gateway
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

_TOOLS_ROOT = Path(__file__).resolve().parents[2]  # .../tools
for _name in ("mathematical_engine", "fixture_scene", "qualitative_research"):
    _p = str(_TOOLS_ROOT / _name)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from feature_engineering.inference import FixtureError  # noqa: E402
from model.serving import ModelNotTrainedError, get_bundle, predict_fixture  # noqa: E402
from research.assemble import research_fixture  # noqa: E402
from scene.assemble import research_scene  # noqa: E402
from scene.draw import FixtureNotFoundError  # noqa: E402

logger = logging.getLogger("mcp_gateway")

mcp = FastMCP(
    "nrl-sports-prediction-tools",
    instructions=(
        "Fact tools for an NRL sports prediction agent. "
        "Call set_fixture_scene first for kickoff/venue/weather/officials. "
        "Then research_fixture_news (pass agent-authored queries) and "
        "predict_match (wire venue/kickoff/weather from scene). "
        "These tools return structured facts only — they do not pick a winner."
    ),
)


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
def set_fixture_scene(
    home_team: str,
    away_team: str,
    season: int | None = None,
    round_number: int | None = None,
    force_refresh: bool = False,
) -> str:
    """Resolve an upcoming NRL fixture from nrl.com and attach kickoff weather.

    Call this FIRST before research or predict.

    Args:
        home_team: NRL nickName (e.g. Eels).
        away_team: NRL nickName (e.g. Panthers).
        season: Optional season year; defaults to current AU year.
        round_number: Optional round; discovers from draw if omitted.
        force_refresh: Bypass day cache.

    Returns JSON with fixture (kickoff, venue, officials, team_lists),
    weather.at_kickoff, weather.math_weather_label (Fine/Rain/unknown) for
    predict_match, and sources. Soft-fails team lists/weather. Does not pick
    a winner.
    """
    try:
        result = research_scene(
            home_team,
            away_team,
            season=season,
            round_number=round_number,
            force_refresh=force_refresh,
        )
        return _json(result)
    except FixtureNotFoundError as e:
        return _json({"error": "fixture_not_found", "detail": str(e)})
    except Exception as e:
        logger.exception("set_fixture_scene failed")
        return _json({"error": "scene_failed", "detail": str(e)})


@mcp.tool()
def research_fixture_news(
    home_team: str,
    away_team: str,
    kickoff: str,
    round_number: int | None = None,
    venue: str | None = None,
    force_refresh: bool = False,
    max_age_days: int = 10,
    queries: list[str] | None = None,
) -> str:
    """Multi-channel qualitative research (injuries, Late Mail, form headlines).

    Facts only — no winner prediction. Prefer kickoff/venue/round from
    set_fixture_scene. Do NOT use this tool for weather, venue, kickoff, or
    match officials (scene owns those).

    Args:
        home_team / away_team: NRL nickNames.
        kickoff: ISO datetime from scene.
        round_number / venue: Optional context from scene.
        force_refresh: Bypass day cache.
        max_age_days: Recency window before kickoff.
        queries: Optional agent-authored search strings (max 6). When omitted,
            built-in templates are used. Prefer injuries / Late Mail / form —
            not weather or referee queries.

    Returns JSON with channels, items (with body_excerpt), queries_run,
    filter_summary. Soft-fails individual channels.
    """
    try:
        result = research_fixture(
            home_team,
            away_team,
            kickoff,
            round_number=round_number,
            venue=venue,
            force_refresh=force_refresh,
            max_age_days=max_age_days,
            queries=queries,
        )
        return _json(result)
    except Exception as e:
        logger.exception("research_fixture_news failed")
        return _json({"error": "research_failed", "detail": str(e)})


@mcp.tool()
def predict_match(
    home_team: str,
    away_team: str,
    venue: str,
    kickoff: str,
    weather: str | None = None,
    top_k: int = 5,
) -> str:
    """Calibrated XGBoost home-win probability + SHAP drivers for one fixture.

    Deterministic math — no news analysis. Orchestrator should pass venue,
    kickoff, and weather=math_weather_label from set_fixture_scene.

    Args:
        home_team / away_team: NRL nickNames.
        venue: Stadium name from scene.
        kickoff: ISO datetime from scene.
        weather: Prefer Fine/Rain/unknown from scene.math_weather_label.
        top_k: Number of SHAP drivers to return (does not change the probability).

    Returns JSON with prediction, home_win_probability, probability,
    shap_explanations, and fixture echo.
    """
    try:
        result = predict_fixture(
            home_team=home_team,
            away_team=away_team,
            venue=venue,
            kickoff=kickoff,
            weather=weather,
            top_k=top_k,
        )
        return _json(result)
    except ModelNotTrainedError as e:
        return _json({"error": "model_not_trained", "detail": str(e)})
    except FixtureError as e:
        return _json({"error": "fixture_error", "detail": str(e)})
    except Exception as e:
        logger.exception("predict_match failed")
        return _json({"error": "predict_failed", "detail": str(e)})


@mcp.tool()
def tools_health() -> str:
    """Report gateway + tool package readiness (model artifacts, versions).

    Ops/debug only — not required for a prediction run.
    """
    from scene import TOOL_NAME as SCENE_NAME, TOOL_VERSION as SCENE_VERSION
    from research import TOOL_NAME as RESEARCH_NAME, TOOL_VERSION as RESEARCH_VERSION

    health: dict[str, Any] = {
        "gateway": "nrl-sports-prediction-tools",
        "tools": {
            "set_fixture_scene": {"package": SCENE_NAME, "version": SCENE_VERSION},
            "research_fixture_news": {
                "package": RESEARCH_NAME,
                "version": RESEARCH_VERSION,
            },
            "predict_match": {"package": "mathematical_engine"},
        },
    }
    try:
        bundle = get_bundle()
        health["tools"]["predict_match"]["model"] = {
            "status": "ok",
            "trained_at": bundle.metrics.get("trained_at"),
            "n_training_rows": bundle.metrics.get("n_training_rows"),
            "loaded_at": bundle.loaded_at.isoformat(),
        }
    except ModelNotTrainedError as e:
        health["tools"]["predict_match"]["model"] = {
            "status": "not_trained",
            "detail": str(e),
        }
    except Exception as e:
        health["tools"]["predict_match"]["model"] = {
            "status": "error",
            "detail": str(e),
        }
    return _json(health)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    mcp.run()


if __name__ == "__main__":
    main()
