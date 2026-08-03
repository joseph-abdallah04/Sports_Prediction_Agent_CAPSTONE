"""Verifier: deterministic checklist + LLM audit (no tool recalls)."""

from __future__ import annotations

import json
import logging
from typing import Any

from agent_app.config import Settings
from agent_app.judgement import label_shap_drivers
from agent_app.llm import chat_completion, parse_json_object
from agent_app.prompts import VERIFIER_SYSTEM

logger = logging.getLogger(__name__)

# Judgement confidence must track the model probability for the picked side.
CONFIDENCE_TOLERANCE = 0.10
CONFIDENCE_CEILING = 0.85
CONFIDENCE_CEILING_AGAINST_MODEL = 0.60

_WEATHER_WORDS = ("weather", "rain", "wet", "wind", "humid", "heat", "temperature")

# Evidence budget for the audit packet. The verifier must see the same article
# text the judge saw, bounded so the prompt stays well inside context.
_VERIFIER_MAX_ITEMS = 12
_VERIFIER_BODY_CHARS = 900
_VERIFIER_PROMPT_CHARS = 40000


def _weather_supported_by_shap(shap_explanations: Any) -> bool:
    """True if any SHAP driver string actually references weather."""
    if not isinstance(shap_explanations, dict):
        return False
    for drivers in shap_explanations.values():
        for driver in drivers or []:
            if any(w in str(driver).lower() for w in _WEATHER_WORDS):
                return True
    return False


def _check_judgement_grounding(
    judgement: dict[str, Any],
    math_resp: dict[str, Any] | None,
    research_resp: dict[str, Any] | None,
) -> list[str]:
    """Evidence-grounding rules that can be decided in code, not by an LLM."""
    issues: list[str] = []
    factors = [f for f in (judgement.get("key_factors") or []) if isinstance(f, dict)]

    # Weather may only be a key factor when SHAP actually surfaced it. The model
    # finds match-day weather near-irrelevant, but the scene reports it, and the
    # judge has a standing habit of promoting it to a headline reason.
    if math_resp and not math_resp.get("error"):
        if not _weather_supported_by_shap(math_resp.get("shap_explanations")):
            for factor in factors:
                if any(w in str(factor.get("detail", "")).lower() for w in _WEATHER_WORDS):
                    issues.append("weather_cited_without_shap_support")
                    break

    # If research produced usable items, the judgement must actually use one.
    if research_resp and not research_resp.get("error"):
        items = research_resp.get("items") or []
        if items and not any(f.get("source") == "research" for f in factors):
            issues.append("no_research_key_factor_despite_items")

    # Confidence must stay anchored to the calibrated model probability.
    confidence = judgement.get("confidence")
    home_prob = (math_resp or {}).get("home_win_probability")
    winner = judgement.get("winner")
    if (
        isinstance(confidence, (int, float))
        and isinstance(home_prob, (int, float))
        and winner in ("home", "away")
    ):
        model_prob = home_prob if winner == "home" else 1.0 - home_prob
        against_model = model_prob < 0.5
        ceiling = (
            CONFIDENCE_CEILING_AGAINST_MODEL if against_model else CONFIDENCE_CEILING
        )
        if confidence > ceiling:
            issues.append(f"confidence_above_ceiling:{confidence:.2f}>{ceiling:.2f}")
        elif not against_model and abs(confidence - model_prob) > CONFIDENCE_TOLERANCE:
            issues.append(
                f"confidence_detached_from_model:{confidence:.2f}_vs_{model_prob:.2f}"
            )
    return issues


def checklist_verify(ledger: dict[str, Any]) -> dict[str, Any]:
    """Deterministic structural and grounding checks on the run ledger."""
    issues: list[str] = []
    tools = {t.get("tool_name") for t in ledger.get("tool_calls") or []}
    for required in ("set_fixture_scene", "research_fixture_news", "predict_match"):
        if required not in tools:
            issues.append(f"missing_tool:{required}")

    scene_resp = None
    predict_req = None
    math_resp = None
    research_resp = None
    for t in ledger.get("tool_calls") or []:
        if t.get("tool_name") == "set_fixture_scene" and t.get("response"):
            scene_resp = t["response"]
        if t.get("tool_name") == "predict_match":
            predict_req = t.get("request") or {}
            if isinstance(t.get("response"), dict):
                math_resp = t["response"]
        if t.get("tool_name") == "research_fixture_news":
            if isinstance(t.get("response"), dict):
                research_resp = t["response"]

    if scene_resp and not scene_resp.get("error"):
        fix = scene_resp.get("fixture") or {}
        weather = (scene_resp.get("weather") or {}).get("math_weather_label")
        if predict_req:
            if predict_req.get("venue") != fix.get("venue"):
                issues.append("predict_venue_mismatch_scene")
            if predict_req.get("kickoff") != fix.get("kickoff"):
                issues.append("predict_kickoff_mismatch_scene")
            if weather and predict_req.get("weather") != weather:
                issues.append("predict_weather_not_from_scene_label")

    judgement = ledger.get("final_judgement") or {}
    for key in ("winner", "confidence", "summary", "key_factors"):
        if key not in judgement:
            issues.append(f"judgement_missing:{key}")
    if judgement.get("winner") not in (None, "home", "away"):
        issues.append("judgement_winner_invalid")

    factors = judgement.get("key_factors") or []
    if isinstance(factors, list) and factors:
        for i, f in enumerate(factors):
            if not isinstance(f, dict) or not f.get("detail"):
                issues.append(f"key_factor_empty:{i}")

    if judgement:
        issues.extend(_check_judgement_grounding(judgement, math_resp, research_resp))

    return {"pass": len(issues) == 0, "issues": issues}


def _fixture_teams(ledger: dict[str, Any]) -> tuple[str | None, str | None]:
    """Home and away nickNames from the scene call, for labelling SHAP drivers."""
    for t in ledger.get("tool_calls") or []:
        if t.get("tool_name") == "set_fixture_scene" and isinstance(t.get("response"), dict):
            fixture = t["response"].get("fixture") or {}
            return fixture.get("home_team"), fixture.get("away_team")
    return None, None


def llm_audit(settings: Settings, ledger: dict[str, Any]) -> dict[str, Any]:
    """LLM verifier subagent — read-only on an abridged ledger."""
    teams = _fixture_teams(ledger)
    abridged = {
        "request": ledger.get("request"),
        "tool_calls": [
            {
                "tool_name": t.get("tool_name"),
                "error": t.get("error"),
                "request": t.get("request"),
                "response_keys": list((t.get("response") or {}).keys())
                if isinstance(t.get("response"), dict)
                else None,
                "response_snippet": _snip_response(
                    t.get("tool_name"), t.get("response"), teams
                ),
            }
            for t in (ledger.get("tool_calls") or [])
        ],
        "final_judgement": ledger.get("final_judgement"),
        "research_loop": ledger.get("research_loop"),
    }
    messages = [
        {"role": "system", "content": VERIFIER_SYSTEM},
        {
            "role": "user",
            "content": "Audit this ledger:\n"
            + json.dumps(abridged, default=str)[:_VERIFIER_PROMPT_CHARS],
        },
    ]
    raw = chat_completion(settings, messages, temperature=0.1)
    try:
        data = parse_json_object(raw)
    except Exception as e:
        logger.warning("Verifier LLM JSON parse failed; retrying once: %s", e)
        messages = [
            *messages,
            {"role": "assistant", "content": raw},
            {
                "role": "user",
                "content": (
                    "Your previous reply was invalid or truncated JSON. "
                    "Reply again with ONLY a complete JSON object: "
                    '{"pass": true|false, "issues": [...], "instruction": "..."}'
                ),
            },
        ]
        raw = chat_completion(settings, messages, temperature=0.1)
        try:
            data = parse_json_object(raw)
        except Exception as e2:
            logger.warning("Verifier LLM JSON parse failed after retry: %s", e2)
            return {
                "pass": True,
                "issues": [],
                "instruction": "",
                "parse_error": str(e2),
                "raw": raw[:1000],
            }
    return {
        "pass": bool(data.get("pass", True)),
        "issues": list(data.get("issues") or []),
        "instruction": str(data.get("instruction") or ""),
    }


def _snip_response(
    tool_name: str | None,
    response: Any,
    teams: tuple[str | None, str | None] = (None, None),
) -> Any:
    if not isinstance(response, dict):
        return None
    if response.get("error"):
        return {"error": response.get("error"), "detail": response.get("detail")}
    if tool_name == "set_fixture_scene":
        f = response.get("fixture") or {}
        return {
            "kickoff": f.get("kickoff"),
            "venue": f.get("venue"),
            "math_weather_label": (response.get("weather") or {}).get("math_weather_label"),
        }
    if tool_name == "predict_match":
        return {
            "home_win_probability": response.get("home_win_probability"),
            "prediction": response.get("prediction"),
            "shap_drivers": label_shap_drivers(
                response.get("shap_explanations"), *teams
            ),
        }
    if tool_name == "research_fixture_news":
        items = [i for i in (response.get("items") or []) if isinstance(i, dict)]
        # The verifier is asked whether each player/injury claim traces to a
        # research item, so it needs the article text, not just the headline.
        # Shown titles alone it reliably declares true, sourced facts to be
        # hallucinations (DD-33).
        return {
            "n_items": len(items),
            "items": [
                {
                    "title": i.get("title"),
                    "source": i.get("source_domain") or i.get("channel"),
                    "published": i.get("published"),
                    "body_excerpt": (i.get("body_excerpt") or "")[:_VERIFIER_BODY_CHARS],
                }
                for i in items[:_VERIFIER_MAX_ITEMS]
            ],
            "queries_run": response.get("queries_run"),
        }
    return None


def should_recalibrate(
    checklist: dict[str, Any],
    audit: dict[str, Any],
) -> tuple[bool, list[str], str]:
    issues = list(checklist.get("issues") or []) + list(audit.get("issues") or [])
    fail = (not checklist.get("pass")) or (not audit.get("pass"))
    instruction = audit.get("instruction") or ""
    if fail and not instruction and issues:
        instruction = (
            "Address these issues and re-output judgement JSON without new tools: "
            + "; ".join(issues[:5])
        )
    return fail, issues, instruction
