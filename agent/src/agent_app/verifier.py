"""Verifier: deterministic checklist + LLM audit (no tool recalls)."""

from __future__ import annotations

import json
import logging
from typing import Any

from agent_app.config import Settings
from agent_app.llm import chat_completion, parse_json_object
from agent_app.prompts import VERIFIER_SYSTEM

logger = logging.getLogger(__name__)


def checklist_verify(ledger: dict[str, Any]) -> dict[str, Any]:
    """Deterministic structural checks on the run ledger."""
    issues: list[str] = []
    tools = {t.get("tool_name") for t in ledger.get("tool_calls") or []}
    for required in ("set_fixture_scene", "research_fixture_news", "predict_match"):
        if required not in tools:
            issues.append(f"missing_tool:{required}")

    scene_resp = None
    predict_req = None
    for t in ledger.get("tool_calls") or []:
        if t.get("tool_name") == "set_fixture_scene" and t.get("response"):
            scene_resp = t["response"]
        if t.get("tool_name") == "predict_match":
            predict_req = t.get("request") or {}

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

    # Soft citation check: each key_factor should mention a known token
    factors = judgement.get("key_factors") or []
    if isinstance(factors, list) and factors:
        for i, f in enumerate(factors):
            if not isinstance(f, dict) or not f.get("detail"):
                issues.append(f"key_factor_empty:{i}")

    return {"pass": len(issues) == 0, "issues": issues}


def llm_audit(settings: Settings, ledger: dict[str, Any]) -> dict[str, Any]:
    """LLM verifier subagent — read-only on an abridged ledger."""
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
                "response_snippet": _snip_response(t.get("tool_name"), t.get("response")),
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
            "content": "Audit this ledger:\n" + json.dumps(abridged, default=str)[:24000],
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


def _snip_response(tool_name: str | None, response: Any) -> Any:
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
            "shap_explanations": response.get("shap_explanations"),
        }
    if tool_name == "research_fixture_news":
        items = response.get("items") or []
        return {
            "n_items": len(items),
            "titles": [i.get("title") for i in items[:8] if isinstance(i, dict)],
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
