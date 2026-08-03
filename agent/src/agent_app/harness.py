"""Batch results harness: run a whole round, then score it against actuals.

A single fixture tells you almost nothing about whether the agent is any good.
This runs every Premiership fixture in a round from the nrl.com draw, records
what the agent and the math model each predicted, and later scores both against
the real results alongside the always-back-the-home-team baseline.

Two steps, run days apart:

    # before the round
    uv run python -m agent_app.harness run --season 2026 --round 23

    # after the last game
    uv run python -m agent_app.harness score --season 2026 --round 23

Predictions are written to agent_runs/rounds/<season>-R<round>/predictions.json,
so scoring reads back exactly what was predicted beforehand and cannot be
back-fitted. Scoring adds scored.json and a readable summary.md beside it.

Budget roughly an hour for a full round on local Ollama (8 fixtures at 6-10
minutes each); far less on a hosted provider.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure src layout imports work when run as a module.
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scene.draw import fixture_result, list_round_fixtures
from scene.http_client import RateLimitedHttpClient

from agent_app.config import PROVIDERS, Settings, get_settings, missing_credentials
from agent_app.orchestrator import run_prediction
from agent_app.report import render_round_summary
from agent_app.run_paths import round_dir

logger = logging.getLogger("harness")

# Clamp before taking logs so one confident miss cannot dominate the metric.
_EPS = 1e-6


def round_file(settings: Settings, season: int, round_number: int) -> Path:
    """Pre-kickoff predictions for a round."""
    return round_dir(Path(settings.agent_runs_dir), season, round_number) / "predictions.json"


def _home_win_probability(winner: str | None, confidence: Any) -> float | None:
    """Convert the judge's (winner, confidence) into a home-win probability."""
    if winner not in ("home", "away") or not isinstance(confidence, (int, float)):
        return None
    return float(confidence) if winner == "home" else 1.0 - float(confidence)


def run_round(
    season: int,
    round_number: int,
    *,
    settings: Settings,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Run the agent over every fixture in a round and persist the predictions."""
    client = RateLimitedHttpClient()
    fixtures = list_round_fixtures(client, season, round_number)
    logger.info("Round %d, season %d: %d fixtures", round_number, season, len(fixtures))

    predictions: list[dict[str, Any]] = []
    for i, card in enumerate(fixtures, start=1):
        home, away = card["home_team"], card["away_team"]
        logger.info("--- [%d/%d] %s v %s ---", i, len(fixtures), home, away)
        result = run_prediction(
            home,
            away,
            season=season,
            round_number=round_number,
            force_refresh=force_refresh,
            settings=settings,
        )
        judgement = result.get("final_judgement") or {}
        predictions.append(
            {
                "home_team": home,
                "away_team": away,
                "kickoff": card.get("kickoff_raw"),
                "venue": card.get("venue"),
                "run_id": result.get("run_id"),
                "ledger_path": result.get("ledger_path"),
                "error": result.get("error"),
                "agent_winner": judgement.get("winner"),
                "agent_confidence": judgement.get("confidence"),
                "math_home_win_probability": result.get("math_home_win_probability"),
            }
        )

    payload = {
        "season": season,
        "round_number": round_number,
        "predicted_at": datetime.now(timezone.utc).isoformat(),
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "predictions": predictions,
    }
    path = round_file(settings, season, round_number)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    logger.info("Wrote %d predictions to %s", len(predictions), path)
    return payload


def _metrics(rows: list[dict[str, Any]], prob_key: str) -> dict[str, Any]:
    """Accuracy / Brier / log loss for one predictor over scored fixtures."""
    scored = [r for r in rows if r.get(prob_key) is not None]
    if not scored:
        return {"n": 0}
    correct = sum(
        1
        for r in scored
        if (r[prob_key] >= 0.5) == (r["actual_winner"] == "home")
    )
    brier = sum(
        (r[prob_key] - (1.0 if r["actual_winner"] == "home" else 0.0)) ** 2
        for r in scored
    ) / len(scored)
    log_loss = -sum(
        math.log(
            min(max(
                r[prob_key] if r["actual_winner"] == "home" else 1.0 - r[prob_key],
                _EPS,
            ), 1 - _EPS)
        )
        for r in scored
    ) / len(scored)
    return {
        "n": len(scored),
        "accuracy": correct / len(scored),
        "brier": brier,
        "log_loss": log_loss,
    }


def score_round(season: int, round_number: int, *, settings: Settings) -> dict[str, Any]:
    """Score a previously-run round against the actual results."""
    path = round_file(settings, season, round_number)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run 'harness run --season {season} "
            f"--round {round_number}' before the games."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))

    client = RateLimitedHttpClient()
    cards = {
        (c["home_team"], c["away_team"]): c
        for c in list_round_fixtures(client, season, round_number)
    }

    rows: list[dict[str, Any]] = []
    pending, draws = 0, 0
    for pred in payload["predictions"]:
        card = cards.get((pred["home_team"], pred["away_team"]))
        actual = fixture_result(card) if card else None
        if actual is None:
            pending += 1
            continue
        if actual["winner"] == "draw":
            draws += 1
            continue
        rows.append(
            {
                **pred,
                "actual_winner": actual["winner"],
                "actual_score": f"{actual['home_score']}-{actual['away_score']}",
                "margin": actual["margin"],
                "agent_home_prob": _home_win_probability(
                    pred.get("agent_winner"), pred.get("agent_confidence")
                ),
                "math_home_prob": pred.get("math_home_win_probability"),
            }
        )

    home_rate = (
        sum(1 for r in rows if r["actual_winner"] == "home") / len(rows) if rows else 0.0
    )
    report = {
        "season": season,
        "round_number": round_number,
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "n_scored": len(rows),
        "n_pending": pending,
        "n_draws_excluded": draws,
        "home_win_rate": home_rate,
        "agent": _metrics(rows, "agent_home_prob"),
        "math": _metrics(rows, "math_home_prob"),
        "always_home_accuracy": home_rate,
        "fixtures": rows,
    }

    out = path.with_name("scored.json")
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    path.with_name("summary.md").write_text(
        render_round_summary(report), encoding="utf-8"
    )

    print(f"\n=== Season {season}, round {round_number} ===")
    print(f"Scored {len(rows)} fixtures ({pending} not finished, {draws} draws excluded)")
    print(f"\n{'fixture':<26} {'actual':>10} {'agent':>17} {'math':>7}")
    for r in rows:
        agent = (
            f"{r['agent_winner']} {r['agent_confidence']:.2f}"
            if r.get("agent_home_prob") is not None
            else "-"
        )
        math_p = (
            f"{r['math_home_prob']:.2f}" if r.get("math_home_prob") is not None else "-"
        )
        hit = "OK " if (r.get("agent_home_prob") is not None
                        and (r["agent_home_prob"] >= 0.5) ==
                        (r["actual_winner"] == "home")) else "MISS"
        print(f"{r['home_team'] + ' v ' + r['away_team']:<26} "
              f"{r['actual_score']:>10} {agent:>12} {hit:>4} {math_p:>7}")

    print(f"\n{'predictor':<14} {'n':>4} {'accuracy':>9} {'brier':>8} {'log_loss':>9}")
    for name in ("agent", "math"):
        m = report[name]
        if m.get("n"):
            print(f"{name:<14} {m['n']:>4} {m['accuracy']:>9.3f} "
                  f"{m['brier']:>8.4f} {m['log_loss']:>9.4f}")
    print(f"{'always_home':<14} {len(rows):>4} {home_rate:>9.3f}")
    print(f"\nWrote {out}\n      {out.with_name('summary.md')}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch round runner and scorer")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="run the agent over every fixture in a round")
    run_cmd.add_argument("--season", type=int, required=True)
    run_cmd.add_argument("--round", type=int, required=True, dest="round_number")
    run_cmd.add_argument("--force-refresh", action="store_true")

    score_cmd = sub.add_parser("score", help="score a previously-run round")
    score_cmd.add_argument("--season", type=int, required=True)
    score_cmd.add_argument("--round", type=int, required=True, dest="round_number")

    parser.add_argument("--provider", choices=PROVIDERS, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    if not args.verbose:
        for noisy in ("LiteLLM", "litellm", "httpx", "httpcore", "openai", "primp",
                      "urllib3", "asyncio"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    overrides: dict[str, str] = {}
    if args.provider:
        overrides["llm_provider"] = args.provider
    if args.model:
        overrides["llm_model"] = args.model

    settings = get_settings(**overrides)
    warning = missing_credentials(settings)
    if warning:
        logger.error("%s", warning)
        return 2

    if args.command == "run":
        run_round(
            args.season,
            args.round_number,
            settings=settings,
            force_refresh=args.force_refresh,
        )
    else:
        score_round(args.season, args.round_number, settings=settings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
