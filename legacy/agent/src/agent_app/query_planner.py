"""LLM query planner for research_fixture_news."""

from __future__ import annotations

import json
import logging
from typing import Any

from agent_app.config import Settings
from agent_app.llm import chat_completion, parse_json_object
from agent_app.prompts import QUERY_PLAN_SYSTEM, QUERY_REFINE_SYSTEM

logger = logging.getLogger(__name__)


def plan_queries(
    settings: Settings,
    *,
    scene: dict[str, Any],
    user_question: str,
    max_queries: int = 6,
) -> list[str]:
    fixture = scene.get("fixture") or {}
    slim = {
        "home_team": fixture.get("home_team"),
        "away_team": fixture.get("away_team"),
        "round_number": fixture.get("round_number"),
        "kickoff": fixture.get("kickoff"),
        "venue": fixture.get("venue"),
        "math_weather_label": (scene.get("weather") or {}).get("math_weather_label"),
    }
    user = (
        f"User question: {user_question}\n\n"
        f"Scene (abridged): {json.dumps(slim)}\n\n"
        f"Propose up to {max_queries} queries."
    )
    raw = chat_completion(
        settings,
        [
            {"role": "system", "content": QUERY_PLAN_SYSTEM},
            {"role": "user", "content": user},
        ],
        step="query_plan",
    )
    data = parse_json_object(raw)
    queries = data.get("queries") or []
    if not isinstance(queries, list):
        raise ValueError("query planner did not return queries list")
    return [str(q).strip() for q in queries if str(q).strip()][:max_queries]


def refine_queries(
    settings: Settings,
    *,
    scene: dict[str, Any],
    previous_queries: list[str],
    gate_diagnostics: dict[str, Any],
    max_queries: int = 4,
) -> list[str]:
    fixture = scene.get("fixture") or {}
    user = (
        f"Fixture: {fixture.get('home_team')} v {fixture.get('away_team')} "
        f"round {fixture.get('round_number')}\n"
        f"Previous queries: {json.dumps(previous_queries)}\n"
        f"Gate failure: {json.dumps(gate_diagnostics)}\n"
        f"Propose up to {max_queries} sharper queries."
    )
    raw = chat_completion(
        settings,
        [
            {"role": "system", "content": QUERY_REFINE_SYSTEM},
            {"role": "user", "content": user},
        ],
        step="research_refine",
    )
    data = parse_json_object(raw)
    queries = data.get("queries") or []
    return [str(q).strip() for q in queries if str(q).strip()][:max_queries]
