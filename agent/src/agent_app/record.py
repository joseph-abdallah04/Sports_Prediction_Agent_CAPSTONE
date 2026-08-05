"""The short version of a run: `record.json` plus a row in the running log.

The ledger holds everything, which is exactly what makes it a poor place to read
a single number out of on a Sunday evening. This derives a small, flat record of
the things needed to write up a round — the prediction, the confidence, the
model's own probability, what research was used, what the verifier said — and
appends one row per prediction to a cumulative CSV.

Both are computed from the ledger, with no LLM and no network, so a record can
always be rebuilt from a run that has already happened.

The CSV is **append-only**. It ends in columns the agent never writes
(`actual_winner`, the control systems, `notes`) which are there to be filled in
by hand; because existing lines are never rewritten, those edits survive every
later run.
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

LOG_FILENAME = "predictions_log.csv"

_LOCAL_TZ = ZoneInfo("Australia/Sydney")

# Written by the agent.
_MACHINE_COLUMNS = (
    "run_id",
    "predicted_at_utc",
    "predicted_at_local",
    "season",
    "round",
    "home_team",
    "away_team",
    "venue",
    "kickoff_local",
    "hours_before_kickoff",
    "predicted_winner",
    "predicted_side",
    "confidence",
    "agent_home_win_prob",
    "math_home_win_prob",
    "math_prediction",
    "research_items_kept",
    "research_queries",
    "research_refine_triggered",
    "verifier_ran",
    "checklist_pass",
    "audit_pass",
    "recalibration_triggered",
    "confidence_before_recalibration",
    "llm_provider",
    "llm_model",
    "wall_seconds",
    "failed",
    "ledger_path",
)

# Never written by the agent — yours to fill in after the round.
_MANUAL_COLUMNS = (
    "actual_winner",
    "actual_home_score",
    "actual_away_score",
    "vanilla_llm_winner",
    "vanilla_llm_confidence",
    "statsinsider_home_prob",
    "notes",
)

CSV_COLUMNS = _MACHINE_COLUMNS + _MANUAL_COLUMNS


def _parse(raw: Any) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def _local(raw: Any) -> str | None:
    dt = _parse(raw)
    return dt.astimezone(_LOCAL_TZ).isoformat() if dt else None


def _tool_responses(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Last response per tool, so a refined re-search wins over the first pass."""
    out: dict[str, dict[str, Any]] = {}
    for call in ledger.get("tool_calls") or []:
        response = call.get("response")
        if isinstance(response, dict):
            out[call.get("tool_name")] = response
    return out


def _home_win_probability(side: Any, confidence: Any) -> float | None:
    """The judge's confidence expressed as P(home win), for scoring."""
    if side not in ("home", "away") or not isinstance(confidence, (int, float)):
        return None
    return round(float(confidence) if side == "home" else 1.0 - float(confidence), 4)


def _domain(url: Any) -> str | None:
    """Publisher domain from a URL, which is what a citation needs."""
    text = str(url or "")
    if "//" not in text:
        return None
    host = text.split("//", 1)[1].split("/", 1)[0].lower()
    return host[4:] if host.startswith("www.") else host or None


def _drivers(math: dict[str, Any]) -> dict[str, list[str]]:
    shap = math.get("shap_explanations")
    if not isinstance(shap, dict):
        return {}
    return {
        str(group): [str(d) for d in (drivers or [])][:5]
        for group, drivers in shap.items()
    }


def build_record(ledger: dict[str, Any], ledger_path: Path | None = None) -> dict[str, Any]:
    """Flatten a ledger into the handful of facts a write-up actually needs."""
    request = ledger.get("request") or {}
    judgement = ledger.get("final_judgement") or {}
    responses = _tool_responses(ledger)
    scene = responses.get("set_fixture_scene") or {}
    fixture = scene.get("fixture") or {}
    math = responses.get("predict_match") or {}
    research = responses.get("research_fixture_news") or {}
    research_loop = ledger.get("research_loop") or {}
    verifier = ledger.get("verifier_loop") or {}
    checklist = verifier.get("checklist") or {}
    audit = verifier.get("llm_audit") or {}

    home_team = fixture.get("home_team") or request.get("home_team")
    away_team = fixture.get("away_team") or request.get("away_team")
    side = judgement.get("winner")
    confidence = judgement.get("confidence")

    started, finished = _parse(ledger.get("created_at")), _parse(ledger.get("updated_at"))
    kickoff = _parse(fixture.get("kickoff"))
    hours_before = (
        round((kickoff - finished).total_seconds() / 3600, 1)
        if kickoff and finished
        else None
    )

    items = [i for i in (research.get("items") or []) if isinstance(i, dict)]

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": ledger.get("run_id"),
        "run": {
            # The run's own end time, so the gap to kickoff is the real one.
            "predicted_at_utc": ledger.get("updated_at"),
            "predicted_at_local": _local(ledger.get("updated_at")),
            "started_at_utc": ledger.get("created_at"),
            "wall_seconds": (
                round((finished - started).total_seconds(), 1)
                if started and finished
                else None
            ),
            "hours_before_kickoff": hours_before,
            "llm_provider": request.get("llm_provider"),
            "llm_model": request.get("llm_model"),
            "failed": bool(ledger.get("error")),
            "error": ledger.get("error"),
        },
        "fixture": {
            "season": fixture.get("season") or request.get("season"),
            "round": fixture.get("round_number") or request.get("round_number"),
            "home_team": home_team,
            "away_team": away_team,
            "venue": fixture.get("venue"),
            "kickoff": fixture.get("kickoff"),
            "kickoff_local": _local(fixture.get("kickoff")),
            "weather": (scene.get("weather") or {}).get("math_weather_label"),
        },
        "prediction": {
            "predicted_winner": (
                home_team if side == "home" else away_team if side == "away" else None
            ),
            "predicted_side": side,
            "confidence": confidence,
            "home_win_probability": _home_win_probability(side, confidence),
        },
        # Kept separate from the prediction: the agent is free to disagree with
        # it, and the two are scored independently (DD-41).
        "math_model": {
            "home_win_probability": math.get("home_win_probability"),
            "prediction": math.get("prediction"),
            "shap_drivers": _drivers(math),
        },
        "research": {
            "queries_run": research.get("queries_run") or research_loop.get("queries_before"),
            "items_kept": len(items),
            "refine_triggered": bool(research_loop.get("triggered")),
            "gate_passed": research_loop.get("result_ok"),
            "items": [
                {
                    "title": i.get("title"),
                    "source": _domain(i.get("url")),
                    "channel": i.get("channel"),
                    "tier": i.get("source_tier"),
                    "category": i.get("category"),
                    "published_at": i.get("published_at"),
                    "age_hours": i.get("age_hours"),
                    "url": i.get("url"),
                }
                for i in items
            ],
        },
        "verification": {
            "verifier_ran": verifier.get("verifier_ran"),
            "checklist_pass": checklist.get("pass"),
            "checklist_issues": checklist.get("issues") or [],
            "audit_pass": audit.get("pass"),
            "audit_issues": audit.get("issues") or [],
            "checks": [
                {"check": c.get("check"), "verdict": c.get("verdict"),
                 "evidence": c.get("evidence")}
                for c in (audit.get("checks") or [])
                if isinstance(c, dict)
            ],
            "recalibration_triggered": bool(verifier.get("recalibration_triggered")),
            "confidence_before_recalibration": (
                (verifier.get("judgement_before") or {}).get("confidence")
                if verifier.get("recalibration_triggered")
                else None
            ),
        },
        "reasoning": {
            "summary": judgement.get("summary"),
            "key_factors": judgement.get("key_factors") or [],
            "disagreements_with_math": judgement.get("disagreements_with_math"),
        },
        "paths": {
            "ledger": str(ledger_path) if ledger_path else None,
            "summary": str(ledger_path.with_name("summary.md")) if ledger_path else None,
        },
    }


def _csv_row(record: dict[str, Any]) -> dict[str, Any]:
    run = record.get("run") or {}
    fixture = record.get("fixture") or {}
    prediction = record.get("prediction") or {}
    math = record.get("math_model") or {}
    research = record.get("research") or {}
    verification = record.get("verification") or {}
    queries = research.get("queries_run") or []
    return {
        "run_id": record.get("run_id"),
        "predicted_at_utc": run.get("predicted_at_utc"),
        "predicted_at_local": run.get("predicted_at_local"),
        "season": fixture.get("season"),
        "round": fixture.get("round"),
        "home_team": fixture.get("home_team"),
        "away_team": fixture.get("away_team"),
        "venue": fixture.get("venue"),
        "kickoff_local": fixture.get("kickoff_local"),
        "hours_before_kickoff": run.get("hours_before_kickoff"),
        "predicted_winner": prediction.get("predicted_winner"),
        "predicted_side": prediction.get("predicted_side"),
        "confidence": prediction.get("confidence"),
        "agent_home_win_prob": prediction.get("home_win_probability"),
        "math_home_win_prob": math.get("home_win_probability"),
        "math_prediction": math.get("prediction"),
        "research_items_kept": research.get("items_kept"),
        "research_queries": " | ".join(str(q) for q in queries),
        "research_refine_triggered": research.get("refine_triggered"),
        "verifier_ran": verification.get("verifier_ran"),
        "checklist_pass": verification.get("checklist_pass"),
        "audit_pass": verification.get("audit_pass"),
        "recalibration_triggered": verification.get("recalibration_triggered"),
        "confidence_before_recalibration": verification.get(
            "confidence_before_recalibration"
        ),
        "llm_provider": run.get("llm_provider"),
        "llm_model": run.get("llm_model"),
        "wall_seconds": run.get("wall_seconds"),
        "failed": run.get("failed"),
        "ledger_path": (record.get("paths") or {}).get("ledger"),
    }


def append_to_log(log_path: Path, record: dict[str, Any]) -> None:
    """Append one row. Existing lines, including hand-typed ones, are untouched."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not log_path.exists() or log_path.stat().st_size == 0
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        writer.writerow(_csv_row(record))


def write_record(
    ledger_path: Path,
    ledger: dict[str, Any],
    *,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """Write `record.json` beside the ledger and append to the running log."""
    record = build_record(ledger, ledger_path)
    path = ledger_path.with_name("record.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str, ensure_ascii=False)
        f.write("\n")
    tmp.replace(path)

    if log_path is not None:
        append_to_log(log_path, record)
    return record
