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

An NRL round runs Thursday to Sunday, so `run` is **incremental**: it appends to
predictions.json, skips fixtures already predicted, and refuses to predict a
fixture whose kickoff has passed. That means you can predict each game on its
own match day, when the team lists are out, without a later run overwriting an
earlier game's pre-kickoff record:

    # Wednesday, for Thursday's game
    uv run python -m agent_app.harness run --season 2026 --round 23 --only Titans

    # Friday, for whatever is still ahead of kickoff
    uv run python -m agent_app.harness run --season 2026 --round 23

Every prediction carries its own `predicted_at`, so the gap between prediction
and kickoff is auditable per fixture rather than per round.

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
from zoneinfo import ZoneInfo

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

# Kickoffs are stored in UTC but read by someone thinking in match-day time.
_LOCAL_TZ = ZoneInfo("Australia/Sydney")


def round_file(settings: Settings, season: int, round_number: int) -> Path:
    """Pre-kickoff predictions for a round."""
    return round_dir(Path(settings.agent_runs_dir), season, round_number) / "predictions.json"


def _home_win_probability(winner: str | None, confidence: Any) -> float | None:
    """Convert the judge's (winner, confidence) into a home-win probability."""
    if winner not in ("home", "away") or not isinstance(confidence, (int, float)):
        return None
    return float(confidence) if winner == "home" else 1.0 - float(confidence)


def _fixture_key(home: str, away: str) -> str:
    return f"{(home or '').strip().lower()}|{(away or '').strip().lower()}"


def _parse_kickoff(raw: Any) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def _matches_only(card: dict[str, Any], only: list[str]) -> bool:
    if not only:
        return True
    blob = f"{card.get('home_team')} {card.get('away_team')}".lower()
    return any(term.strip().lower() in blob for term in only if term.strip())


def run_round(
    season: int,
    round_number: int,
    *,
    settings: Settings,
    force_refresh: bool = False,
    only: list[str] | None = None,
    repredict: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Predict the fixtures in a round that are still ahead of kickoff.

    Incremental by design. A round spans four days, so predicting every game at
    once means the Sunday fixtures are judged on Wednesday's team lists. This
    merges into any existing predictions file instead of replacing it, so each
    game can be predicted on its own match day without disturbing the record of
    what was predicted for the games already played.
    """
    now = now or datetime.now(timezone.utc)
    client = RateLimitedHttpClient()
    fixtures = list_round_fixtures(client, season, round_number)
    path = round_file(settings, season, round_number)

    existing: dict[str, Any] = {}
    by_key: dict[str, dict[str, Any]] = {}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        for row in existing.get("predictions") or []:
            by_key[_fixture_key(row.get("home_team"), row.get("away_team"))] = row

    todo: list[dict[str, Any]] = []
    for card in fixtures:
        home, away = card["home_team"], card["away_team"]
        key = _fixture_key(home, away)
        label = f"{home} v {away}"
        if not _matches_only(card, only or []):
            continue
        prior = by_key.get(key)
        if prior and not prior.get("error") and not repredict:
            logger.info("skip  %-28s already predicted %s", label, prior.get("predicted_at"))
            continue
        kickoff = _parse_kickoff(card.get("kickoff_raw"))
        if kickoff and kickoff <= now:
            # Predicting a played game is not a prediction, and writing one into
            # this file would quietly invalidate the whole scorecard.
            logger.warning("skip  %-28s kickoff has passed (%s)", label, kickoff.isoformat())
            continue
        todo.append(card)

    logger.info(
        "Round %d, season %d: %d fixtures, %d to predict now",
        round_number,
        season,
        len(fixtures),
        len(todo),
    )
    if not todo:
        logger.info("Nothing to do. %s", path if path.exists() else "No predictions yet.")
        return existing or {"season": season, "round_number": round_number, "predictions": []}

    for i, card in enumerate(todo, start=1):
        home, away = card["home_team"], card["away_team"]
        logger.info("--- [%d/%d] %s v %s ---", i, len(todo), home, away)
        result = run_prediction(
            home,
            away,
            season=season,
            round_number=round_number,
            force_refresh=force_refresh,
            settings=settings,
        )
        judgement = result.get("final_judgement") or {}
        by_key[_fixture_key(home, away)] = {
            "home_team": home,
            "away_team": away,
            "kickoff": card.get("kickoff_raw"),
            "venue": card.get("venue"),
            # Per fixture, so the gap to kickoff is auditable game by game.
            "predicted_at": datetime.now(timezone.utc).isoformat(),
            "run_id": result.get("run_id"),
            "ledger_path": result.get("ledger_path"),
            "error": result.get("error"),
            "agent_winner": judgement.get("winner"),
            "agent_confidence": judgement.get("confidence"),
            "math_home_win_probability": result.get("math_home_win_probability"),
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
        }

    # Draw order, so the file reads like the round.
    order = [_fixture_key(c["home_team"], c["away_team"]) for c in fixtures]
    predictions = [by_key[k] for k in order if k in by_key]

    payload = {
        "season": season,
        "round_number": round_number,
        "first_predicted_at": existing.get("first_predicted_at")
        or datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "predictions": predictions,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    logger.info(
        "Wrote %d of %d fixtures to %s", len(predictions), len(fixtures), path
    )
    return payload


def plan_round(
    season: int,
    round_number: int,
    *,
    settings: Settings,
    only: list[str] | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Print the round, each fixture's kickoff, and what a run would do.

    Answers "what is still ahead of kickoff, and when do I need to run it" in a
    couple of seconds, without spending an hour of inference to find out.
    """
    now = now or datetime.now(timezone.utc)
    fixtures = list_round_fixtures(RateLimitedHttpClient(), season, round_number)
    path = round_file(settings, season, round_number)
    by_key: dict[str, dict[str, Any]] = {}
    if path.exists():
        for row in json.loads(path.read_text(encoding="utf-8")).get("predictions") or []:
            by_key[_fixture_key(row.get("home_team"), row.get("away_team"))] = row

    rows: list[dict[str, Any]] = []
    logger.info("Season %d, round %d — times shown in %s", season, round_number, _LOCAL_TZ)
    logger.info("%-26s %-18s %10s  %s", "Fixture", "Kickoff", "In", "Status")
    for card in fixtures:
        home, away = card["home_team"], card["away_team"]
        label = f"{home} v {away}"
        kickoff = _parse_kickoff(card.get("kickoff_raw"))
        prior = by_key.get(_fixture_key(home, away))
        if not _matches_only(card, only or []):
            status = "filtered out by --only"
        elif prior and not prior.get("error"):
            status = f"predicted {prior.get('predicted_at') or 'earlier'}"
        elif kickoff and kickoff <= now:
            status = "SKIPPED — kickoff has passed"
        else:
            status = "would predict now"
        hours = (kickoff - now).total_seconds() / 3600 if kickoff else None
        logger.info(
            "%-26s %-18s %10s  %s",
            label,
            kickoff.astimezone(_LOCAL_TZ).strftime("%a %d %b %H:%M") if kickoff else "unknown",
            f"{hours:.0f}h" if hours is not None else "?",
            status,
        )
        rows.append({"fixture": label, "kickoff": card.get("kickoff_raw"), "status": status})
    return rows


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

    # Shared flags live on the subcommands, so they can be written after it:
    # `harness run --season … --provider openai` rather than the argparse
    # default of requiring them before the subcommand, which reads backwards.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--provider", choices=PROVIDERS, default=None)
    common.add_argument("--model", default=None)
    common.add_argument("-v", "--verbose", action="store_true")

    run_cmd = sub.add_parser(
        "run",
        parents=[common],
        help="predict the fixtures in a round that are still ahead of kickoff",
    )
    run_cmd.add_argument("--season", type=int, required=True)
    run_cmd.add_argument("--round", type=int, required=True, dest="round_number")
    run_cmd.add_argument("--force-refresh", action="store_true",
                         help="bypass the research and scene caches")
    run_cmd.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="TEAM",
        help="limit to fixtures involving TEAM; repeatable "
             "(e.g. --only Titans --only Warriors)",
    )
    run_cmd.add_argument(
        "--repredict",
        action="store_true",
        help="re-run fixtures already predicted, replacing their entries",
    )
    run_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="list what would be predicted, without calling the LLM",
    )

    score_cmd = sub.add_parser(
        "score", parents=[common], help="score a previously-run round"
    )
    score_cmd.add_argument("--season", type=int, required=True)
    score_cmd.add_argument("--round", type=int, required=True, dest="round_number")

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
        if args.dry_run:
            plan_round(args.season, args.round_number, settings=settings, only=args.only)
            return 0
        run_round(
            args.season,
            args.round_number,
            settings=settings,
            force_refresh=args.force_refresh,
            only=args.only,
            repredict=args.repredict,
        )
    else:
        score_round(args.season, args.round_number, settings=settings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
