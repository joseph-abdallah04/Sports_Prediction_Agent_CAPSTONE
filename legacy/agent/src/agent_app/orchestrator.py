"""Constrained-pipeline Orchestrator."""

from __future__ import annotations

import concurrent.futures
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_app.config import Settings, get_settings
from agent_app import ledger as ledger_mod
from agent_app import llm as llm_mod
from agent_app import record as record_mod
from agent_app import tools_bridge
from agent_app.judgement import recalibrate_judgement, start_judgement_session
from agent_app.query_planner import plan_queries, refine_queries
from agent_app.report import render_run_summary, render_thinking
from agent_app.research_gate import research_ok
from agent_app.run_paths import fixture_run_dir
from agent_app.verifier import checklist_verify, llm_audit, should_recalibrate

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stage(n: int, total: int, msg: str) -> None:
    logger.info("[%d/%d] %s", n, total, msg)


def _secs(start: datetime, end: datetime | None = None) -> float:
    end = end or _now()
    return (end - start).total_seconds()


def run_prediction(
    home_team: str,
    away_team: str,
    *,
    user_question: str | None = None,
    season: int | None = None,
    round_number: int | None = None,
    force_refresh: bool = False,
    settings: Settings | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Full agent run; returns final judgement and writes ledger to disk."""
    settings = settings or get_settings()
    run_id = run_id or ledger_mod.new_run_id()
    question = user_question or f"Who wins {home_team} vs {away_team}?"

    request = {
        "home_team": home_team,
        "away_team": away_team,
        "season": season,
        "round_number": round_number,
        "force_refresh": force_refresh,
        "user_question": question,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
    }
    ledger = ledger_mod.create_ledger(run_id, request)
    # Same list object the LLM client appends to — rewritten into thinking.md
    # on every persist so a mid-run open shows scratchpads so far.
    thinking_trace: list[dict[str, Any]] = ledger["thinking_trace"]
    thinking_token = llm_mod.bind_thinking_trace(thinking_trace)
    # Provisional: refined once the scene reports the real season and round, so
    # the folder name says which fixture it was even when the CLI wasn't told.
    run_dir = fixture_run_dir(
        Path(settings.agent_runs_dir), run_id, home_team, away_team, season, round_number
    )
    ledger_path = run_dir / "ledger.json"
    total = 6
    run_t0 = _now()

    recorded = False

    def persist() -> None:
        ledger_mod.save_ledger(ledger_path, ledger)
        try:
            (ledger_path.parent / "summary.md").write_text(
                render_run_summary(ledger), encoding="utf-8"
            )
        except Exception as e:  # a broken summary must never lose the ledger
            logger.debug("Could not write summary.md: %s", e)
        try:
            (ledger_path.parent / "thinking.md").write_text(
                render_thinking(ledger), encoding="utf-8"
            )
        except Exception as e:
            logger.debug("Could not write thinking.md: %s", e)

    def finalise() -> None:
        """Write record.json and append one row to the running log.

        Called on every exit path but only ever acts once, so a run that dies at
        the scene still leaves a row saying so — a prediction missing from the
        log is indistinguishable from a round nobody ran.
        """
        nonlocal recorded
        if recorded:
            return
        recorded = True
        try:
            record_mod.write_record(
                ledger_path,
                ledger,
                log_path=Path(settings.agent_runs_dir) / record_mod.LOG_FILENAME,
            )
        except Exception as e:  # never lose a completed run over its summary row
            logger.warning("Could not write record.json or log row: %s", e)

    logger.info(
        "=== Agent run start run_id=%s model=%s/%s ===",
        run_id,
        settings.llm_provider,
        settings.llm_model,
    )
    logger.info("Question: %s", question)

    try:
        # 1) Scene
        _stage(1, total, f"Scene: resolve fixture {home_team} vs {away_team}")
        t0 = _now()
        scene = tools_bridge.set_fixture_scene(
            home_team,
            away_team,
            season=season,
            round_number=round_number,
            force_refresh=force_refresh,
        )
        t1 = _now()
        ledger_mod.append_tool_call(
            ledger,
            tool_name="set_fixture_scene",
            request={
                "home_team": home_team,
                "away_team": away_team,
                "season": season,
                "round_number": round_number,
                "force_refresh": force_refresh,
            },
            response=scene,
            started_at=t0,
            finished_at=t1,
            error=scene.get("error"),
        )
        scene_fixture = scene.get("fixture") or {}
        run_dir = fixture_run_dir(
            Path(settings.agent_runs_dir),
            run_id,
            home_team,
            away_team,
            scene_fixture.get("season") or season,
            scene_fixture.get("round_number") or round_number,
        )
        ledger_path = run_dir / "ledger.json"
        persist()
        if scene.get("error"):
            logger.error("Scene failed: %s", scene)
            ledger["error"] = scene
            persist()
            finalise()
            return {"run_id": run_id, "ledger_path": str(ledger_path), "error": scene}

        fixture = scene.get("fixture") or {}
        kickoff = fixture.get("kickoff")
        venue = fixture.get("venue")
        weather_label = (scene.get("weather") or {}).get("math_weather_label")
        logger.info(
            "Scene OK in %.1fs (cache_hit=%s): Round %s | %s @ %s | weather=%s",
            _secs(t0, t1),
            scene.get("cache_hit"),
            fixture.get("round_number"),
            kickoff,
            venue,
            weather_label,
        )
        if not kickoff or not venue:
            err = {"error": "scene_incomplete", "detail": "Missing kickoff or venue"}
            ledger["error"] = err
            persist()
            finalise()
            return {"run_id": run_id, "ledger_path": str(ledger_path), "error": err}

        # 2) Query plan
        _stage(2, total, "Query plan: LLM authors research queries")
        t0 = _now()
        queries = plan_queries(
            settings,
            scene=scene,
            user_question=question,
            max_queries=settings.max_agent_queries,
        )
        logger.info(
            "Query plan OK in %.1fs (%d queries):",
            _secs(t0),
            len(queries),
        )
        for i, q in enumerate(queries, 1):
            logger.info("  Q%d: %s", i, q)
        ledger_mod.append_agent_step(
            ledger, step="query_plan", payload={"queries": queries}
        )
        persist()

        # 3) Research (+ optional refine) and math from scene (parallel first pass)
        _stage(
            3,
            total,
            "Research ∥ Math: search news + predict_match (parallel)",
        )

        def _research(q: list[str] | None, refresh: bool) -> dict[str, Any]:
            return tools_bridge.research_fixture_news(
                fixture.get("home_team") or home_team,
                fixture.get("away_team") or away_team,
                kickoff,
                round_number=fixture.get("round_number") or round_number,
                venue=venue,
                force_refresh=refresh or force_refresh,
                queries=q,
            )

        def _predict() -> dict[str, Any]:
            return tools_bridge.predict_match(
                fixture.get("home_team") or home_team,
                fixture.get("away_team") or away_team,
                venue,
                kickoff,
                weather=weather_label,
            )

        t_r0 = _now()
        t_p0 = _now()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            fut_r = pool.submit(_research, queries, False)
            fut_p = pool.submit(_predict)
            research = fut_r.result()
            math = fut_p.result()
        t_r1 = _now()
        t_p1 = _now()

        filt = research.get("filter_summary") or {}
        items = research.get("items") or []
        ch = research.get("channels") or {}
        logger.info(
            "Research OK in %.1fs (cache_hit=%s): kept=%s | dropped stale=%s noise=%s "
            "irrelevant=%s wrong_round=%s",
            _secs(t_r0, t_r1),
            research.get("cache_hit"),
            filt.get("kept", len(items)),
            filt.get("dropped_stale"),
            filt.get("dropped_noise"),
            filt.get("dropped_irrelevant"),
            filt.get("dropped_wrong_round"),
        )
        for name, summary in ch.items():
            if not isinstance(summary, dict):
                continue
            logger.info(
                "  channel %-16s status=%-12s kept=%s%s",
                name,
                summary.get("status"),
                summary.get("items_kept"),
                f" err={summary.get('error')}" if summary.get("error") else "",
            )
        for i, item in enumerate(items[:8], 1):
            if isinstance(item, dict):
                logger.info(
                    "  keep#%d [%s/%s] %s",
                    i,
                    item.get("channel"),
                    item.get("source_tier"),
                    (item.get("title") or "")[:100],
                )

        logger.info(
            "Math OK in %.1fs: %s | P(home win)=%s | P(away≈)=%s",
            _secs(t_p0, t_p1),
            math.get("prediction"),
            math.get("home_win_probability"),
            math.get("probability"),
        )
        shap = math.get("shap_explanations") or {}
        for label, key in (
            ("+ toward home", "positive_drivers"),
            ("- toward away", "negative_drivers"),
        ):
            drivers = shap.get(key) or []
            if drivers:
                logger.info("  SHAP %s: %s", label, "; ".join(drivers[:3]))

        ledger_mod.append_tool_call(
            ledger,
            tool_name="research_fixture_news",
            request={
                "home_team": fixture.get("home_team") or home_team,
                "away_team": fixture.get("away_team") or away_team,
                "kickoff": kickoff,
                "round_number": fixture.get("round_number") or round_number,
                "venue": venue,
                "queries": queries,
                "force_refresh": force_refresh,
            },
            response=research,
            started_at=t_r0,
            finished_at=t_r1,
            error=research.get("error"),
        )
        ledger_mod.append_tool_call(
            ledger,
            tool_name="predict_match",
            request={
                "home_team": fixture.get("home_team") or home_team,
                "away_team": fixture.get("away_team") or away_team,
                "venue": venue,
                "kickoff": kickoff,
                "weather": weather_label,
            },
            response=math,
            started_at=t_p0,
            finished_at=t_p1,
            error=math.get("error"),
        )
        persist()

        ok, diag = research_ok(research)
        research_loop: dict[str, Any] = {
            "triggered": False,
            "gate_first": diag,
            "queries_before": queries,
            "queries_after": None,
            "result_ok": ok,
        }
        logger.info(
            "Research gate: ok=%s (items_with_body=%s official/nrl=%s availability=%s)",
            ok,
            diag.get("kept_items_with_body"),
            diag.get("has_official_or_nrl_news"),
            diag.get("has_availability_keyword_hit"),
        )
        if (not ok) and settings.max_research_loops >= 1:
            logger.info("Research refine loop: gate failed → sharper queries + re-search")
            refined = refine_queries(
                settings,
                scene=scene,
                previous_queries=queries,
                gate_diagnostics=diag,
                max_queries=min(4, settings.max_agent_queries),
            )
            for i, q in enumerate(refined, 1):
                logger.info("  refine Q%d: %s", i, q)
            t0 = _now()
            research2 = _research(refined, True)
            ledger_mod.append_tool_call(
                ledger,
                tool_name="research_fixture_news",
                request={
                    "home_team": fixture.get("home_team") or home_team,
                    "away_team": fixture.get("away_team") or away_team,
                    "kickoff": kickoff,
                    "queries": refined,
                    "force_refresh": True,
                    "loop": "research_refine",
                },
                response=research2,
                started_at=t0,
                finished_at=_now(),
                error=research2.get("error"),
            )
            ok2, diag2 = research_ok(research2)
            research = research2
            research_loop.update(
                {
                    "triggered": True,
                    "reason": diag.get("fail_reasons"),
                    "queries_after": refined,
                    "gate_after": diag2,
                    "result_ok": ok2,
                }
            )
            logger.info(
                "Research refine done in %.1fs: ok=%s kept_bodies=%s",
                _secs(t0),
                ok2,
                diag2.get("kept_items_with_body"),
            )
            ledger_mod.append_agent_step(
                ledger, step="research_refine", payload=research_loop
            )
        else:
            logger.info("Research refine loop: skipped (gate passed or disabled)")
        ledger["research_loop"] = research_loop
        persist()

        # 4) Judgement session
        _stage(4, total, "Judgement: LLM synthesises scene + research + math")
        n_research = len(research.get("items") or [])
        logger.info(
            "Feeding judge: research_items=%d math_pred=%s P(home)=%s",
            n_research,
            math.get("prediction"),
            math.get("home_win_probability"),
        )
        t0 = _now()
        session, judgement = start_judgement_session(
            settings,
            scene=scene,
            research=research,
            math=math,
            user_question=question,
        )
        logger.info(
            "Judgement OK in %.1fs: winner=%s confidence=%s",
            _secs(t0),
            judgement.get("winner"),
            judgement.get("confidence"),
        )
        for f in (judgement.get("key_factors") or [])[:6]:
            if isinstance(f, dict):
                logger.info("  factor [%s] %s", f.get("source"), f.get("detail"))
        ledger["final_judgement"] = judgement
        ledger_mod.append_agent_step(
            ledger, step="judgement", payload={"judgement": judgement}
        )
        persist()

        # 5) Verifier + optional in-session recalibrate
        _stage(5, total, "Verifier: checklist + LLM audit")
        t0 = _now()
        checklist = checklist_verify(ledger)
        logger.info(
            "Checklist: pass=%s issues=%s",
            checklist.get("pass"),
            checklist.get("issues") or [],
        )
        audit = (
            llm_audit(settings, ledger)
            if settings.verifier_enabled
            else {
                "ran": False,
                "pass": True,
                "checks": [],
                "issues": [],
                "instruction": "",
            }
        )
        logger.info(
            "LLM audit: pass=%s issues=%s instruction=%r",
            audit.get("pass"),
            audit.get("issues") or [],
            (audit.get("instruction") or "")[:120],
        )
        for check in audit.get("checks") or []:
            logger.info(
                "  check %-24s %-15s %s",
                check.get("check"),
                check.get("verdict"),
                (check.get("evidence") or "")[:100],
            )
        ledger_mod.append_agent_step(
            ledger,
            step="verifier_audit",
            payload={"checklist": checklist, "llm_audit": audit},
        )
        fail, issues, instruction = should_recalibrate(checklist, audit)
        verifier_loop: dict[str, Any] = {
            # "verifier_ran" is whether the checks happened;
            # "recalibration_triggered" is whether they sent the judge back.
            # A clean run is ran=True, triggered=False — the common case, and
            # easy to misread as "the verifier never ran" if it has one flag.
            "verifier_ran": bool(settings.verifier_enabled),
            "recalibration_triggered": False,
            "checklist": checklist,
            "llm_audit": audit,
            "instruction": instruction,
            "judgement_before": judgement,
            "judgement_after": None,
        }
        if fail and settings.max_verifier_loops >= 1 and settings.verifier_enabled:
            logger.info("Verifier recalibrate: in-session re-judge (no new tools)")
            before = judgement
            judgement = recalibrate_judgement(
                session, issues=issues, instruction=instruction
            )
            ledger["final_judgement"] = judgement
            verifier_loop.update(
                {
                    "recalibration_triggered": True,
                    "issues": issues,
                    "judgement_after": judgement,
                }
            )
            logger.info(
                "Recalibrated: winner=%s → %s | confidence=%s → %s",
                before.get("winner"),
                judgement.get("winner"),
                before.get("confidence"),
                judgement.get("confidence"),
            )
            ledger_mod.append_agent_step(
                ledger,
                step="verifier_recalibrate",
                payload={
                    "issues": issues,
                    "instruction": instruction,
                    "before": before,
                    "after": judgement,
                },
            )
        else:
            logger.info("Verifier recalibrate: skipped (audit/checklist passed)")
        ledger["verifier_loop"] = verifier_loop
        persist()
        finalise()

        _stage(6, total, "Done")
        logger.info(
            "=== Final: winner=%s confidence=%s | total %.1fs ===",
            judgement.get("winner"),
            judgement.get("confidence"),
            _secs(run_t0),
        )
        logger.info("  ledger  %s", ledger_path)
        logger.info("  summary %s", ledger_path.with_name("summary.md"))
        logger.info("  thinking %s", ledger_path.with_name("thinking.md"))
        logger.info("  record  %s", ledger_path.with_name("record.json"))
        logger.info(
            "  log     %s", Path(settings.agent_runs_dir) / record_mod.LOG_FILENAME
        )

        return {
            "run_id": run_id,
            "ledger_path": str(ledger_path),
            "record_path": str(ledger_path.with_name("record.json")),
            "thinking_path": str(ledger_path.with_name("thinking.md")),
            "final_judgement": judgement,
            "research_loop": research_loop,
            "verifier_loop": verifier_loop,
            "scene_fixture": {
                "home_team": fixture.get("home_team"),
                "away_team": fixture.get("away_team"),
                "kickoff": kickoff,
                "venue": venue,
                "weather": weather_label,
            },
            "math_home_win_probability": math.get("home_win_probability"),
        }
    except Exception as e:
        logger.exception("Agent run failed")
        ledger["error"] = {"error": "agent_failed", "detail": str(e)}
        persist()
        finalise()
        return {
            "run_id": run_id,
            "ledger_path": str(ledger_path),
            "thinking_path": str(ledger_path.with_name("thinking.md")),
            "error": ledger["error"],
        }
    finally:
        llm_mod.unbind_thinking_trace(thinking_token)
