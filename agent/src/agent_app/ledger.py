"""Run ledger — full observability for Verifier and humans."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]


def new_call_id() -> str:
    return uuid.uuid4().hex[:12]


def create_ledger(run_id: str, request: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "run_id": run_id,
        "created_at": now,
        "updated_at": now,
        "request": request,
        "tool_calls": [],
        "agent_steps": [],
        "research_loop": None,
        "verifier_loop": None,
        "final_judgement": None,
        "error": None,
    }


def touch(ledger: dict[str, Any]) -> None:
    ledger["updated_at"] = datetime.now(timezone.utc).isoformat()


def append_tool_call(
    ledger: dict[str, Any],
    *,
    tool_name: str,
    request: dict[str, Any],
    response: dict[str, Any] | None,
    started_at: datetime,
    finished_at: datetime,
    error: str | None = None,
) -> dict[str, Any]:
    record = {
        "call_id": new_call_id(),
        "tool_name": tool_name,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "finished_at": finished_at.astimezone(timezone.utc).isoformat(),
        "duration_ms": int((finished_at - started_at).total_seconds() * 1000),
        "request": request,
        "response": response,
        "error": error,
    }
    ledger.setdefault("tool_calls", []).append(record)
    touch(ledger)
    return record


def append_agent_step(
    ledger: dict[str, Any],
    *,
    step: str,
    payload: dict[str, Any],
) -> None:
    ledger.setdefault("agent_steps", []).append(
        {
            "step": step,
            "at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
    )
    touch(ledger)


SCHEMA_VERSION = 2

# Read order, most-summarised first. Anything not listed is appended, so a new
# key can never be silently dropped from the record.
_KEY_ORDER = (
    "schema_version",
    "run_id",
    "at_a_glance",
    "created_at",
    "updated_at",
    "request",
    "error",
    "final_judgement",
    "research_loop",
    "verifier_loop",
    "agent_steps",
    "tool_calls",
)


def _at_a_glance(ledger: dict[str, Any]) -> dict[str, Any]:
    """A few lines answering 'what happened' without scrolling.

    Purely derived from data already in the ledger — it summarises, it never
    replaces, so the record stays complete for auditing.
    """
    request = ledger.get("request") or {}
    judgement = ledger.get("final_judgement") or {}
    responses = {
        call.get("tool_name"): (call.get("response") or {})
        for call in ledger.get("tool_calls") or []
        if isinstance(call.get("response"), dict)
    }
    scene = responses.get("set_fixture_scene", {})
    fixture = scene.get("fixture") or {}
    math = responses.get("predict_match", {})
    research = responses.get("research_fixture_news", {})
    verifier = ledger.get("verifier_loop") or {}

    winner = judgement.get("winner")
    return {
        "fixture": f"{request.get('home_team')} v {request.get('away_team')}",
        "round": fixture.get("round_number"),
        "kickoff": fixture.get("kickoff"),
        "venue": fixture.get("venue"),
        "predicted_winner": (
            request.get("home_team") if winner == "home"
            else request.get("away_team") if winner == "away"
            else None
        ),
        "confidence": judgement.get("confidence"),
        "model_home_win_probability": math.get("home_win_probability"),
        "model_prediction": math.get("prediction"),
        "research_items_kept": len(research.get("items") or []),
        "research_refine_triggered": (ledger.get("research_loop") or {}).get("triggered"),
        "verifier_checklist_pass": (verifier.get("checklist") or {}).get("pass"),
        "verifier_audit_pass": (verifier.get("llm_audit") or {}).get("pass"),
        "recalibrated": bool(verifier.get("triggered")),
        "llm": f"{request.get('llm_provider')}/{request.get('llm_model')}",
        "failed": bool(ledger.get("error")),
    }


def save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    touch(ledger)
    ledger["schema_version"] = SCHEMA_VERSION
    ledger["at_a_glance"] = _at_a_glance(ledger)
    ordered = {k: ledger[k] for k in _KEY_ORDER if k in ledger}
    ordered.update({k: v for k, v in ledger.items() if k not in ordered})

    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ordered, f, indent=2, default=str, ensure_ascii=False)
        f.write("\n")
    tmp.replace(path)
