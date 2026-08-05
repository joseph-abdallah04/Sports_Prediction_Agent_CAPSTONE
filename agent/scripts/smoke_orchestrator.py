"""Offline end-to-end smoke test of the control loop.

Runs `run_prediction` with the fact tools and the LLM replaced by stubs, so
every stage executes — scene, query plan, research, math, judgement, verifier,
recalibration, and both output files — in about a second and with no network.

The point is to catch the class of bug that otherwise only shows up eleven
minutes into a real run: a renamed function, a changed ledger key, a stage that
crashes on a field it no longer gets. Before a round, run this first.

    uv run python scripts/smoke_orchestrator.py

Three scenarios: a clean run where the verifier passes, one where the judge
returns an over-confident pick so the recalibration loop has to fire, and a
four-day round to prove the harness appends rather than replaces.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from agent_app import llm as llm_mod
from agent_app import orchestrator, query_planner, tools_bridge, verifier
from agent_app.config import get_settings

KICKOFF = "2026-08-06T19:50:00+10:00"
VENUE = "Cbus Super Stadium"

SCENE = {
    "fixture": {
        "home_team": "Titans",
        "away_team": "Cowboys",
        "kickoff": KICKOFF,
        "venue": VENUE,
        "season": 2026,
        "round_number": 23,
    },
    "weather": {"math_weather_label": "Fine"},
    "venue_profile": {"venue": VENUE},
}

# Field names mirror what the research tool really returns (published_at, not
# published; no source_domain), so the record builder is tested against the
# shape it will actually be handed.
RESEARCH = {
    "items": [
        {
            "title": "NRL Casualty Ward: Round 23 injury list",
            "url": "https://www.nrl.com/news/casualty-ward",
            "channel": "nrl_news",
            "source_tier": "official",
            "category": "Injuries",
            "published_at": "2026-08-03T08:00:00+00:00",
            "age_hours": 1.3,
            "body_excerpt": "Griffin Neame expected return round 23. "
            "John Bateman is named to play.",
        },
        {
            "title": "Titans v Cowboys team lists",
            "url": "https://www.zerotackle.com/titans-cowboys-r23",
            "channel": "google_news_rss",
            "source_tier": "media",
            "category": "Team lists",
            "published_at": "2026-08-02T21:00:00+00:00",
            "age_hours": 12.5,
            "body_excerpt": "Late mail: Reed Mahoney returns for the Cowboys.",
        },
        {
            "title": "Round 23 preview: Titans host Cowboys",
            "url": "https://www.foxsports.com.au/nrl/r23-preview",
            "channel": "duckduckgo",
            "source_tier": "media",
            "category": "Preview",
            "published_at": "2026-08-02T10:00:00+00:00",
            "age_hours": 23.0,
            "body_excerpt": "Both sides are chasing a finals berth.",
        },
    ],
    "queries_run": ["Titans NRL late mail round 23"],
    "channels": {
        "nrl_news": {"status": "ok", "items_kept": 1},
        "duckduckgo": {"status": "ok", "items_kept": 1},
        "google_news_rss": {"status": "ok", "items_kept": 1},
    },
    "filter_summary": {"kept": 3},
}

MATH = {
    "fixture": {"home_team": "Titans", "away_team": "Cowboys"},
    "home_win_probability": 0.5063,
    "prediction": "Home Win",
    "probability": 0.5063,
    "shap_explanations": {
        "positive_drivers": ["Pythagorean form (last 10) (+11% expected-win gap)"],
        "negative_drivers": ["Elo rating advantage (-129 points)"],
    },
}


def _judgement(confidence: float) -> dict:
    return {
        "winner": "home",
        "home_team": "Titans",
        "away_team": "Cowboys",
        "confidence": confidence,
        "summary": "Pythagorean form favours the Titans at home.",
        "key_factors": [
            {
                "source": "math",
                "detail": "Pythagorean form (last 10) (+11% expected-win gap).",
            },
            {
                "source": "research",
                "detail": "Griffin Neame is expected back for the Cowboys (nrl.com).",
            },
        ],
        "disagreements_with_math": "",
    }


AUDIT_PASS = {
    "checks": [
        {"check": name, "verdict": "pass", "evidence": "Matched in the ledger."}
        for name in (
            "sourced_claims",
            "availability_direction",
            "shap_attribution",
            "weather_not_headline",
            "research_used",
            "confidence_justified",
            "driver_proportionality",
            "omitted_math_signals",
        )
    ],
    "pass": True,
    "issues": [],
    "instruction": "",
}


class StubLLM:
    """Answers by stage, inferred from the system prompt it is handed."""

    def __init__(self, first_confidence: float) -> None:
        self.first_confidence = first_confidence
        self.calls: list[str] = []

    def __call__(self, settings, messages, temperature=0.2, **kwargs) -> str:
        system = messages[0].get("content", "")
        last = messages[-1].get("content", "")
        if "Verifier" in system:
            self.calls.append("verifier")
            return json.dumps(AUDIT_PASS)
        if "research queries" in system or "query" in system.lower():
            self.calls.append("query_plan")
            return json.dumps(
                {"queries": ["Titans NRL late mail round 23", "Cowboys NRL injury"]}
            )
        if "recalibrate" in last.lower() or "Verifier feedback" in last:
            self.calls.append("recalibrate")
            return json.dumps(_judgement(0.54))
        self.calls.append("judgement")
        return json.dumps(_judgement(self.first_confidence))


def _install_stubs(stub: StubLLM) -> None:
    tools_bridge.set_fixture_scene = lambda *a, **k: SCENE
    tools_bridge.research_fixture_news = lambda *a, **k: RESEARCH
    tools_bridge.predict_match = lambda *a, **k: MATH
    # chat_completion is imported by name into each caller's namespace.
    llm_mod.chat_completion = stub
    query_planner.chat_completion = stub
    verifier.chat_completion = stub


def _run(runs_dir: Path, *, first_confidence: float) -> dict:
    stub = StubLLM(first_confidence)
    _install_stubs(stub)
    settings = get_settings(agent_runs_dir=str(runs_dir))
    result = orchestrator.run_prediction(
        settings=settings, home_team="Titans", away_team="Cowboys", round_number=23
    )
    result["_stub_calls"] = stub.calls
    return result


def _check(label: str, condition: bool, detail: str = "") -> bool:
    print(f"  {'ok  ' if condition else 'FAIL'} {label}{f' — {detail}' if detail else ''}")
    return condition


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        runs_dir = Path(tmp)

        print("Scenario 1: clean run, verifier passes")
        result = _run(runs_dir, first_confidence=0.54)
        ledger_path = Path(result["ledger_path"])
        ledger = json.loads(ledger_path.read_text())
        v = ledger.get("verifier_loop") or {}
        audit = v.get("llm_audit") or {}
        steps = [s["step"] for s in ledger.get("agent_steps") or []]

        for label, cond, detail in [
            ("run did not error", not ledger.get("error"), str(ledger.get("error"))),
            ("all three tools called",
             {t["tool_name"] for t in ledger["tool_calls"]}
             == {"set_fixture_scene", "research_fixture_news", "predict_match"}, ""),
            ("verifier ran", v.get("verifier_ran") is True, ""),
            ("no recalibration", v.get("recalibration_triggered") is False, ""),
            ("checklist passed", (v.get("checklist") or {}).get("pass") is True,
             str((v.get("checklist") or {}).get("issues"))),
            ("audit reported 8 checks", len(audit.get("checks") or []) == 8,
             str(len(audit.get("checks") or []))),
            ("verifier_audit is an agent step", "verifier_audit" in steps, str(steps)),
            ("summary.md written",
             (ledger_path.parent / "summary.md").exists(), ""),
            ("summary shows the checks table",
             "What the verifier checked"
             in (ledger_path.parent / "summary.md").read_text(), ""),
            ("at_a_glance records the verifier",
             ledger["at_a_glance"].get("verifier_checks_reported") == 8, ""),
            ("run dir is named for the fixture",
             "2026-R23_Titans-v-Cowboys" in str(ledger_path), str(ledger_path)),
        ]:
            failures += not _check(label, cond, detail)

        failures += _check_record(runs_dir, ledger_path, rows=1)

        print("Scenario 2: over-confident judgement, recalibration must fire")
        # Above the ceiling, which is no longer tied to the model probability.
        result = _run(runs_dir, first_confidence=0.99)
        ledger = json.loads(Path(result["ledger_path"]).read_text())
        v = ledger.get("verifier_loop") or {}
        for label, cond, detail in [
            ("checklist caught the confidence",
             any(i.startswith("confidence_above_ceiling")
                 for i in (v.get("checklist") or {}).get("issues") or []),
             str((v.get("checklist") or {}).get("issues"))),
            ("recalibration fired", v.get("recalibration_triggered") is True, ""),
            ("judgement_after recorded", bool(v.get("judgement_after")), ""),
            ("confidence came back in range",
             (v.get("judgement_after") or {}).get("confidence") == 0.54, ""),
            ("recalibrate step logged",
             "verifier_recalibrate" in [s["step"] for s in ledger["agent_steps"]], ""),
        ]:
            failures += not _check(label, cond, detail)

        failures += _check_record(runs_dir, Path(result["ledger_path"]), rows=2)

        print("Scenario 3: harness is incremental across a four-day round")
        failures += _smoke_harness()

    print("\nSMOKE_OK" if not failures else f"\n{failures} CHECK(S) FAILED")
    return 1 if failures else 0


def _check_record(runs_dir: Path, ledger_path: Path, *, rows: int) -> int:
    """record.json holds the write-up numbers, and the log row is appended.

    The log is the capstone dataset, so the two properties that matter are that
    a row lands for every run and that earlier rows are never rewritten — the
    manual columns are typed in by hand and a rewrite would erase them.
    """
    import csv

    from agent_app.record import CSV_COLUMNS

    record_path = ledger_path.with_name("record.json")
    if not record_path.exists():
        return not _check("record.json written", False, str(record_path))
    record = json.loads(record_path.read_text())
    log_path = runs_dir / "predictions_log.csv"
    with open(log_path, newline="", encoding="utf-8") as f:
        log = list(csv.DictReader(f))

    failures = 0
    for label, cond, detail in [
        ("record names the predicted team, not just a side",
         (record["prediction"] or {}).get("predicted_winner") == "Titans",
         str((record["prediction"] or {}).get("predicted_winner"))),
        ("record keeps the model probability separately",
         record["math_model"]["home_win_probability"] == 0.5063, ""),
        ("record converts confidence to P(home win)",
         record["prediction"]["home_win_probability"] is not None, ""),
        ("record lists the research actually used",
         record["research"]["items_kept"] == 3
         and len(record["research"]["items"]) == 3, ""),
        ("research items are citable: domain and date resolved",
         all(i["source"] and i["published_at"]
             for i in record["research"]["items"]),
         str(record["research"]["items"][0])),
        ("record carries the verifier checks",
         len(record["verification"]["checks"]) == 8, ""),
        ("record measures the gap to kickoff",
         record["run"]["hours_before_kickoff"] is not None, ""),
        ("record points back to the ledger",
         record["paths"]["ledger"] == str(ledger_path), ""),
        (f"log has {rows} row(s), appended not replaced", len(log) == rows, str(len(log))),
        ("log columns match the schema",
         list(log[0].keys()) == list(CSV_COLUMNS) if log else False, ""),
        ("manual columns exist and are left empty",
         all(log[-1].get(c) == "" for c in
             ("actual_winner", "vanilla_llm_winner", "statsinsider_home_prob")) if log
         else False, ""),
    ]:
        failures += not _check(label, cond, detail)
    return failures


def _smoke_harness() -> int:
    """A round spans Thu-Sun, so `run` must append, not replace.

    The risk being guarded is silent and severe: a Saturday run that overwrote
    the file would erase the pre-kickoff record of Thursday's game, and the
    scorecard would look fine while measuring nothing.
    """
    from datetime import datetime, timezone

    from agent_app import harness

    cards = [
        {"home_team": "Titans", "away_team": "Cowboys",
         "kickoff_raw": "2026-08-06T09:50:00Z", "venue": "Cbus Super Stadium"},
        {"home_team": "Warriors", "away_team": "Panthers",
         "kickoff_raw": "2026-08-07T08:00:00Z", "venue": "Go Media Stadium"},
        {"home_team": "Storm", "away_team": "Sea Eagles",
         "kickoff_raw": "2026-08-08T05:00:00Z", "venue": "HBF Park"},
        {"home_team": "Raiders", "away_team": "Knights",
         "kickoff_raw": "2026-08-09T04:00:00Z", "venue": "GIO Stadium"},
    ]
    # Friday lunchtime: the first two games are gone, two remain.
    now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
    harness.list_round_fixtures = lambda client, season, rnd: cards
    _install_stubs(StubLLM(0.54))

    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        settings = get_settings(agent_runs_dir=tmp)
        path = harness.round_file(settings, 2026, 23)

        harness.run_round(2026, 23, settings=settings, only=["Storm"], now=now)
        first = json.loads(path.read_text())
        storm_first = first["predictions"][0]["predicted_at"]

        harness.run_round(2026, 23, settings=settings, now=now)
        second = json.loads(path.read_text())
        names = [r["home_team"] for r in second["predictions"]]
        storm = next(r for r in second["predictions"] if r["home_team"] == "Storm")

        for label, cond, detail in [
            ("--only predicted just that fixture",
             [r["home_team"] for r in first["predictions"]] == ["Storm"], ""),
            ("second pass appended rather than replaced",
             names == ["Storm", "Raiders"], str(names)),
            ("played fixtures were refused",
             not {"Titans", "Warriors"} & set(names), str(names)),
            ("earlier prediction kept its timestamp",
             storm["predicted_at"] == storm_first, ""),
            ("every fixture carries predicted_at",
             all(r.get("predicted_at") for r in second["predictions"]), ""),
            ("first_predicted_at survives the second pass",
             second.get("first_predicted_at") == first.get("first_predicted_at"), ""),
        ]:
            failures += not _check(label, cond, detail)
    return failures


if __name__ == "__main__":
    sys.exit(main())
