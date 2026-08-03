"""Ledger-friendly tool I/O records for Orchestrator / Verifier."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def new_call_id() -> str:
    return uuid.uuid4().hex[:12]


def make_tool_call_record(
    *,
    tool_name: str,
    request: dict[str, Any],
    response: dict[str, Any] | None,
    started_at: datetime,
    finished_at: datetime,
    error: str | None = None,
    call_id: str | None = None,
) -> dict[str, Any]:
    duration_ms = int((finished_at - started_at).total_seconds() * 1000)
    return {
        "call_id": call_id or new_call_id(),
        "tool_name": tool_name,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "finished_at": finished_at.astimezone(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "request": request,
        "response": response,
        "error": error,
    }


def append_tool_record(ledger_path: str | Path, record: dict[str, Any]) -> None:
    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            ledger = json.load(f)
    else:
        ledger = {
            "run_id": path.parent.name if path.parent.name else "manual",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tool_calls": [],
            "agent_steps": [],
            "final_judgement": None,
        }
    ledger.setdefault("tool_calls", []).append(record)
    ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)
    tmp.replace(path)
