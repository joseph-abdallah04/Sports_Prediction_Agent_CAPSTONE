"""Judgement session: non-agentic LLM synthesis over tool facts."""

from __future__ import annotations

import json
from typing import Any

from agent_app.config import Settings
from agent_app.llm import ChatSession, parse_json_object
from agent_app.prompts import JUDGEMENT_SYSTEM, RECALIBRATE_USER_TEMPLATE


def _slim_research(research: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    items = []
    for i in (research.get("items") or [])[:limit]:
        if not isinstance(i, dict):
            continue
        items.append(
            {
                "title": i.get("title"),
                "source_tier": i.get("source_tier"),
                "channel": i.get("channel"),
                "url": i.get("url"),
                "body_excerpt": (i.get("body_excerpt") or "")[:800],
            }
        )
    return items


def start_judgement_session(
    settings: Settings,
    *,
    scene: dict[str, Any],
    research: dict[str, Any],
    math: dict[str, Any],
    user_question: str,
) -> tuple[ChatSession, dict[str, Any]]:
    session = ChatSession(settings)
    session.add_system(JUDGEMENT_SYSTEM)
    fixture = scene.get("fixture") or {}
    weather = scene.get("weather") or {}
    packet = {
        "user_question": user_question,
        "scene": {
            "fixture": {
                k: fixture.get(k)
                for k in (
                    "home_team",
                    "away_team",
                    "kickoff",
                    "venue",
                    "round_number",
                    "officials",
                    "team_lists",
                )
            },
            "math_weather_label": weather.get("math_weather_label"),
        },
        "math": {
            "prediction": math.get("prediction"),
            "home_win_probability": math.get("home_win_probability"),
            "probability": math.get("probability"),
            "shap_explanations": math.get("shap_explanations"),
            "error": math.get("error"),
        },
        "research": {
            "error": research.get("error"),
            "queries_run": research.get("queries_run"),
            "filter_summary": research.get("filter_summary"),
            "items": _slim_research(research),
        },
    }
    session.add_user(
        "Produce your prediction JSON from this evidence:\n"
        + json.dumps(packet, default=str)
    )
    raw = session.complete()
    session.add_assistant(raw)
    judgement = parse_json_object(raw)
    return session, judgement


def recalibrate_judgement(
    session: ChatSession,
    *,
    issues: list[str],
    instruction: str,
) -> dict[str, Any]:
    session.add_user(
        RECALIBRATE_USER_TEMPLATE.format(
            issues="\n".join(f"- {x}" for x in issues) or "- (none listed)",
            instruction=instruction or "Reconsider weighting; re-output judgement JSON.",
        )
    )
    raw = session.complete()
    session.add_assistant(raw)
    return parse_json_object(raw)
