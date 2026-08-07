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

# Confidence bounds, deliberately NOT tied to the model probability (DD-41).
# The floor is definitional rather than a calibration rule: confidence is in the
# side the judge picked, so below 0.50 it has contradicted its own winner.
CONFIDENCE_FLOOR = 0.50
CONFIDENCE_CEILING = 0.95

# Evidence budget for the audit packet. The verifier must see the same article
# text the judge saw, bounded so the prompt stays well inside context.
_VERIFIER_MAX_ITEMS = 12
_VERIFIER_BODY_CHARS = 900
_VERIFIER_PROMPT_CHARS = 40000


def _check_judgement_grounding(
    judgement: dict[str, Any],
    research_resp: dict[str, Any] | None,
) -> list[str]:
    """Evidence-grounding rules that can be decided in code, not by an LLM.

    Weather-as-a-headline is *not* checked here. That is a semantic question, and
    a keyword scan once flagged "hamstring strain" as weather because `rain` is
    a substring of `strain`. The LLM audit's `weather_not_headline` check owns
    that rule instead; the checklist sticks to facts decidable from structure.
    """
    issues: list[str] = []
    factors = [f for f in (judgement.get("key_factors") or []) if isinstance(f, dict)]

    # If research produced usable items, the judgement must actually use one.
    if research_resp and not research_resp.get("error"):
        items = research_resp.get("items") or []
        if items and not any(f.get("source") == "research" for f in factors):
            issues.append("no_research_key_factor_despite_items")

    # Confidence is the judge's own number and is deliberately not compared with
    # the model probability: anchoring the two makes the agent's Brier score a
    # restatement of the model's, which would make the comparison circular
    # (DD-41). Only the two bounds are enforced.
    confidence = judgement.get("confidence")
    if isinstance(confidence, (int, float)):
        if confidence < CONFIDENCE_FLOOR:
            # Below the floor the judge has contradicted its own winner, and the
            # harness would convert it into a probability for the other side.
            issues.append(
                f"confidence_below_floor:{confidence:.2f}<{CONFIDENCE_FLOOR:.2f}"
            )
        elif confidence > CONFIDENCE_CEILING:
            issues.append(
                f"confidence_above_ceiling:{confidence:.2f}>{CONFIDENCE_CEILING:.2f}"
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
    research_resp = None
    for t in ledger.get("tool_calls") or []:
        if t.get("tool_name") == "set_fixture_scene" and t.get("response"):
            scene_resp = t["response"]
        if t.get("tool_name") == "predict_match":
            predict_req = t.get("request") or {}
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
        issues.extend(_check_judgement_grounding(judgement, research_resp))

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
    raw = chat_completion(settings, messages, temperature=0.1, step="verifier_audit")
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
        raw = chat_completion(
            settings, messages, temperature=0.1, step="verifier_audit_retry"
        )
        try:
            data = parse_json_object(raw)
        except Exception as e2:
            logger.warning("Verifier LLM JSON parse failed after retry: %s", e2)
            return {
                "ran": True,
                "pass": True,
                "checks": [],
                "issues": [],
                "instruction": "",
                "parse_error": str(e2),
                "raw": raw[:1000],
            }
    return {
        "ran": True,
        "pass": bool(data.get("pass", True)),
        # What the audit examined, kept whether it passed or failed: a verdict
        # with no record of what was checked cannot be reviewed later.
        "checks": _clean_checks(data.get("checks")),
        "issues": list(data.get("issues") or []),
        "instruction": str(data.get("instruction") or ""),
    }


def _clean_checks(checks: Any) -> list[dict[str, str]]:
    """Normalise the audit's per-check report, tolerating a sloppy model."""
    if not isinstance(checks, list):
        return []
    out: list[dict[str, str]] = []
    for entry in checks:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("check") or "").strip()
        if not name:
            continue
        out.append(
            {
                "check": name,
                "verdict": str(entry.get("verdict") or "").strip().lower() or "unknown",
                "evidence": str(entry.get("evidence") or "").strip()[:600],
            }
        )
    return out


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
        standings = response.get("standings") or {}
        return {
            "kickoff": f.get("kickoff"),
            "venue": f.get("venue"),
            "math_weather_label": (response.get("weather") or {}).get("math_weather_label"),
            "standings": standings if standings.get("available") else {
                "available": False,
                "error": standings.get("error"),
            },
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
