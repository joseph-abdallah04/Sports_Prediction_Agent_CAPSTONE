"""Verifier: deterministic checklist + LLM audit (no tool recalls)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from agent_app.config import Settings
from agent_app.judgement import (
    CLEAR_EDGE_ABOVE,
    confidence_copies_math,
    label_shap_drivers,
    loss_reason_specific_flag,
    math_win_probability_for_side,
    mentions_both_teams,
    normalize_research_stance,
    price_quote,
    research_factors_cite_team_news,
)
from agent_app.llm import chat_completion, parse_json_object
from agent_app.prompts import VERIFIER_SYSTEM

logger = logging.getLogger(__name__)

# Confidence bounds. Floor is definitional: below 0.50 the judge has picked
# the other side. Ceiling matches the prompt's "above 0.85 do not use" band.
# Copying the math probability is a separate check: allowed only when
# research_stance is confirms (qualitative news actually backs the pick).
CONFIDENCE_FLOOR = 0.50
CONFIDENCE_CEILING = 0.85

# SHAP rows below this share of total mass are padding; omitting them is not
# a reason to recalibrate.
MATERIAL_SHAP_MIN_PCT = 8
_SHAP_PCT_RE = re.compile(r"\((\d+)% of total\)")

# Evidence budget for the audit packet. The verifier must see the same article
# text the judge saw, bounded so the prompt stays well inside context.
_VERIFIER_MAX_ITEMS = 12
_VERIFIER_BODY_CHARS = 900
_VERIFIER_PROMPT_CHARS = 40000


def _check_judgement_grounding(
    judgement: dict[str, Any],
    research_resp: dict[str, Any] | None,
    math_resp: dict[str, Any] | None = None,
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

    stance = normalize_research_stance(judgement.get("research_stance"))
    if judgement.get("research_stance") not in (None, "") and stance is None:
        issues.append("research_stance_invalid")
    elif stance is None:
        issues.append("research_stance_missing")

    reason = str(judgement.get("strongest_reason_could_lose") or "").strip()
    if not reason:
        issues.append("strongest_reason_could_lose_missing")

    specific = loss_reason_specific_flag(judgement)
    if specific is None:
        issues.append("loss_reason_specific_missing")

    if stance == "confirms" and not research_factors_cite_team_news(factors):
        issues.append("research_stance_confirms_without_team_news")

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
        else:
            math_p = math_win_probability_for_side(
                math_resp, str(judgement.get("winner") or "")
            )
            confirmed = stance == "confirms" and research_factors_cite_team_news(
                factors
            )
            copied = confidence_copies_math(confidence, math_p)
            if copied and not confirmed:
                issues.append("confidence_copied_math_without_research_confirm")
            if confidence > CLEAR_EDGE_ABOVE and not confirmed:
                issues.append("confidence_above_clear_edge_without_research_confirm")
            if stance == "conflicts" and confidence > CLEAR_EDGE_ABOVE:
                issues.append("confidence_too_high_for_research_conflict")
            if stance == "conflicts" and math_p is not None and (
                copied or float(confidence) >= math_p
            ):
                # Two-decimal paste (0.83 vs 0.8306) is keeping the prior.
                issues.append("confidence_not_discounted_despite_research_conflict")
            if specific is True and confidence > CLEAR_EDGE_ABOVE:
                issues.append("confidence_too_high_for_specific_loss_reason")
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
    predict_resp = None
    research_resp = None
    for t in ledger.get("tool_calls") or []:
        if t.get("tool_name") == "set_fixture_scene" and t.get("response"):
            scene_resp = t["response"]
        if t.get("tool_name") == "predict_match":
            predict_req = t.get("request") or {}
            if isinstance(t.get("response"), dict):
                predict_resp = t["response"]
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
        issues.extend(_check_judgement_grounding(judgement, research_resp, predict_resp))

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
        shap = label_shap_drivers(response.get("shap_explanations"), *teams)
        return {
            "home_win_probability": response.get("home_win_probability"),
            "prediction": response.get("prediction"),
            "shap_drivers": shap,
            "material_shap_drivers": material_shap_drivers(shap),
        }
    if tool_name == "research_fixture_news":
        items = [i for i in (response.get("items") or []) if isinstance(i, dict)]
        req = response.get("request") or {}
        home = req.get("home_team") or teams[0] or ""
        away = req.get("away_team") or teams[1] or ""
        # The verifier is asked whether each player/injury claim traces to a
        # research item, so it needs the article text, not just the headline.
        # Shown titles alone it reliably declares true, sourced facts to be
        # hallucinations (DD-33).
        slim_items = []
        for i in items[:_VERIFIER_MAX_ITEMS]:
            body = i.get("body_excerpt") or ""
            title = i.get("title") or ""
            blob = f"{title}\n{body}"
            entry = {
                "title": i.get("title"),
                "source": i.get("source_domain") or i.get("channel"),
                "published": i.get("published"),
                "body_excerpt": body[:_VERIFIER_BODY_CHARS],
            }
            if (not home or not away or mentions_both_teams(blob, home, away)):
                quote = price_quote(body) or price_quote(blob)
                if quote:
                    entry["price_quote"] = quote
            slim_items.append(entry)
        return {
            "n_items": len(items),
            "items": slim_items,
            "queries_run": response.get("queries_run"),
        }
    return None


def material_shap_drivers(shap: Any, *, min_pct: int = MATERIAL_SHAP_MIN_PCT) -> list[str]:
    """Driver lines whose stated share of total SHAP is at least ``min_pct``."""
    if not isinstance(shap, dict):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for key, drivers in shap.items():
        if key == "value_contribution_conflicts":
            continue
        if not isinstance(drivers, list):
            continue
        for line in drivers:
            text = str(line)
            m = _SHAP_PCT_RE.search(text)
            if not m or int(m.group(1)) < min_pct:
                continue
            if text not in seen:
                seen.add(text)
                out.append(text)
    return out


def omitted_math_signals_only(audit: dict[str, Any]) -> bool:
    """True when the LLM audit failed solely on omitted_math_signals."""
    if audit.get("pass"):
        return False
    failing = [
        c
        for c in (audit.get("checks") or [])
        if isinstance(c, dict) and str(c.get("verdict") or "").lower() == "fail"
    ]
    if not failing:
        return False
    return all(c.get("check") == "omitted_math_signals" for c in failing)


def should_recalibrate(
    checklist: dict[str, Any],
    audit: dict[str, Any],
) -> tuple[bool, list[str], str]:
    issues = list(checklist.get("issues") or []) + list(audit.get("issues") or [])
    checklist_fail = not checklist.get("pass")
    audit_fail = not audit.get("pass")
    instruction = audit.get("instruction") or ""
    if checklist_fail:
        fail = True
    elif audit_fail and omitted_math_signals_only(audit):
        fail = False
    else:
        fail = audit_fail
    if fail and not instruction and issues:
        instruction = (
            "Address these issues and re-output judgement JSON without new tools: "
            + "; ".join(issues[:5])
        )
    return fail, issues, instruction
