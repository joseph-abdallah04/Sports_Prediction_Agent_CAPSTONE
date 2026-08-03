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


def save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    touch(ledger)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, default=str)
    tmp.replace(path)
