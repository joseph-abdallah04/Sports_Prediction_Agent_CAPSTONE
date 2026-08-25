"""Human-readable renderings of a run ledger and a round scorecard.

`ledger.json` is the record of truth and nothing is ever removed from it. It is
also several hundred lines of nested JSON, which is the wrong shape for the
question "what did it decide, and why". These functions render the same data as
markdown sitting next to the JSON — a summary, not a substitute.
"""

from __future__ import annotations

from typing import Any


def _tool(ledger: dict[str, Any], name: str) -> dict[str, Any]:
    for call in ledger.get("tool_calls") or []:
        if call.get("tool_name") == name:
            return call
    return {}


def _fmt_pct(value: Any) -> str:
    return f"{float(value):.0%}" if isinstance(value, (int, float)) else "—"


def render_run_summary(ledger: dict[str, Any]) -> str:
    """Markdown summary of one agent run."""
    request = ledger.get("request") or {}
    home = request.get("home_team", "?")
    away = request.get("away_team", "?")
    judgement = ledger.get("final_judgement") or {}
    error = ledger.get("error")

    scene = (_tool(ledger, "set_fixture_scene").get("response") or {})
    fixture = scene.get("fixture") or {}
    math = (_tool(ledger, "predict_match").get("response") or {})
    research_call = _tool(ledger, "research_fixture_news")
    research = research_call.get("response") or {}
    items = [i for i in (research.get("items") or []) if isinstance(i, dict)]

    home_prob = math.get("home_win_probability")
    winner = judgement.get("winner")
    picked = home if winner == "home" else away if winner == "away" else "—"

    lines: list[str] = [
        f"# {home} v {away}",
        "",
        f"- **Run**: `{ledger.get('run_id')}`",
        f"- **When**: {ledger.get('created_at')}",
        f"- **Model**: {request.get('llm_provider')}/{request.get('llm_model')}",
        f"- **Kickoff**: {fixture.get('kickoff') or '—'} at "
        f"{fixture.get('venue') or '—'} (round {fixture.get('round_number') or '—'})",
        "",
    ]

    if error:
        lines += ["## Run failed", "", "```json", str(error), "```", ""]
        return "\n".join(lines)

    if not judgement:
        # Written on every persist, so most of a run this file is a partial.
        lines += [
            "## Run in progress",
            "",
            "No judgement yet. This file is rewritten at every stage, so it is "
            "a live view rather than a final record.",
            "",
        ]
    else:
        lines += [
            "## Verdict",
            "",
            f"**{picked}** to win, confidence {_fmt_pct(judgement.get('confidence'))}.",
            "",
            f"> {judgement.get('summary') or '—'}",
            "",
        ]
        stance = judgement.get("research_stance")
        if stance:
            lines += [f"- **Research vs math:** {stance}"]
        loss = judgement.get("strongest_reason_could_lose")
        if loss:
            lines += [f"- **Strongest reason it could lose:** {loss}"]
        specific = judgement.get("loss_reason_specific")
        if specific is not None:
            lines += [f"- **Loss reason is specific:** {specific}"]
        lines += [
            "",
            "### Key factors",
            "",
        ]
    for factor in judgement.get("key_factors") or []:
        if isinstance(factor, dict):
            lines.append(f"- **{factor.get('source', '?')}** — {factor.get('detail', '')}")
    disagreement = judgement.get("disagreements_with_math")
    if disagreement and str(disagreement).lower() not in ("null", "none", ""):
        lines += ["", f"**Disagreement with the model:** {disagreement}"]

    lines += [
        "",
        "## What the maths said",
        "",
        f"- Prediction: **{math.get('prediction') or '—'}**",
        f"- P({home} win) = **{home_prob:.4f}**" if isinstance(home_prob, (int, float))
        else "- P(home win) unavailable",
        "",
    ]
    shap = math.get("shap_explanations") or {}
    if shap:
        lines.append(f"| Favouring {home} (home) | Favouring {away} (away) |")
        lines.append("| --- | --- |")
        pos = list(shap.get("positive_drivers") or [])
        neg = list(shap.get("negative_drivers") or [])
        for i in range(max(len(pos), len(neg))):
            lines.append(
                f"| {pos[i] if i < len(pos) else ''} | {neg[i] if i < len(neg) else ''} |"
            )
        lines.append("")
        balance = shap.get("attribution_balance") or {}
        if balance:
            lines.append(
                f"- Attribution balance: leans **{balance.get('leans') or '—'}** "
                f"(home {balance.get('total_toward_home')}, "
                f"away {balance.get('total_toward_away')})"
            )
        conflicts = shap.get("value_contribution_conflicts") or []
        if conflicts:
            lines.append("- Value/contribution conflicts:")
            for c in conflicts:
                lines.append(f"  - {c}")
        if balance or conflicts:
            lines.append("")

    standings = scene.get("standings") or {}
    if standings.get("available"):
        lines += _render_standings_section(standings, home, away)
    elif standings:
        lines += [
            "## Ladder standings",
            "",
            f"Unavailable: {standings.get('error') or 'unknown error'}",
            "",
        ]

    summary = research.get("filter_summary") or {}
    lines += [
        "## What the research found",
        "",
        f"{len(items)} items kept"
        + (f" (dropped: {_drop_line(summary)})" if summary else "")
        + ".",
        "",
    ]
    for item in items:
        published = item.get("published_at") or item.get("published") or ""
        source = item.get("source_domain") or item.get("channel") or ""
        title = item.get("title") or item.get("url") or ""
        url = item.get("url") or ""
        lines.append(f"- [{title}]({url})  \n  `{source}` {published}")
    lines.append("")

    lines += ["## Queries the agent wrote", ""]
    for query in research.get("queries_run") or []:
        lines.append(f"- `{query}`")
    lines.append("")

    lines += _render_loops(ledger)
    lines += [
        "---",
        "",
        "Full detail, including every tool request and response, is in "
        "`ledger.json` beside this file. Nothing is omitted there.",
    ]
    return "\n".join(lines)


def _standing_row(team: dict[str, Any] | None) -> str:
    if not isinstance(team, dict):
        return "—"
    pos = team.get("position")
    pd = team.get("points_difference")
    pd_g = team.get("points_difference_per_game")
    w, d, l = team.get("wins"), team.get("drawn"), team.get("lost")
    record = f"{w}-{d}-{l}" if None not in (w, d, l) else "—"
    pd_txt = f"{pd:+d}" if isinstance(pd, int) else str(pd)
    per = f" ({pd_g:+.2f}/g)" if isinstance(pd_g, (int, float)) else ""
    return f"**{team.get('team') or '?'}** — {pos}th · {record} · PD {pd_txt}{per}"


def _render_standings_section(
    standings: dict[str, Any], home: str, away: str
) -> list[str]:
    """Readable ladder block for summary.md (same facts the judge sees)."""
    home_row = standings.get("home") or {}
    away_row = standings.get("away") or {}
    cmp_ = standings.get("comparison") or {}
    lines = [
        "## Ladder standings",
        "",
        f"As at round {standings.get('as_at_round') or '—'} "
        f"([nrl.com]({standings.get('source_url') or '#'})).",
        "",
        f"- {_standing_row(home_row)}",
        f"- {_standing_row(away_row)}",
        "",
        f"- Higher on ladder: **{cmp_.get('higher_on_ladder') or '—'}**",
        f"- Points-difference favours: **{cmp_.get('points_difference_favours') or '—'}** "
        f"(home−away PD/game gap: {cmp_.get('points_difference_per_game_gap')})",
        "",
    ]
    return lines


def _drop_line(summary: dict[str, Any]) -> str:
    parts = [
        f"{key.removeprefix('dropped_')} {value}"
        for key, value in summary.items()
        if key.startswith("dropped_") and value
    ]
    return ", ".join(parts) or "none"


def _verdict(result: Any) -> str:
    """passed / FAILED / not run — a stage that has not happened is not a failure."""
    if result is None:
        return "not run"
    return "passed" if result else "FAILED"


def _render_loops(ledger: dict[str, Any]) -> list[str]:
    lines = ["## Loops", ""]
    research_loop = ledger.get("research_loop")
    if research_loop is None:
        lines.append("- **Research refine**: not run yet")
    else:
        gate = research_loop.get("gate_first") or {}
        lines.append(
            "- **Research refine**: "
            + ("triggered" if research_loop.get("triggered") else "not needed")
            + f" (gate passed: {gate.get('research_ok')}, "
            f"{gate.get('kept_items_with_body')} items with body text)"
        )

    verifier = ledger.get("verifier_loop") or {}
    checklist = verifier.get("checklist") or {}
    audit = verifier.get("llm_audit") or {}
    lines.append(
        f"- **Verifier**: coded checklist {_verdict(checklist.get('pass'))}, "
        f"LLM audit {_verdict(audit.get('pass'))}"
    )
    issues = list(checklist.get("issues") or []) + list(audit.get("issues") or [])
    for issue in issues:
        lines.append(f"    - {issue}")
    if verifier.get("recalibration_triggered"):
        before = (verifier.get("judgement_before") or {})
        after = (verifier.get("judgement_after") or {})
        lines.append(
            f"    - recalibrated: {before.get('winner')} "
            f"{before.get('confidence')} → {after.get('winner')} "
            f"{after.get('confidence')}"
        )
    elif verifier:
        lines.append("    - no recalibration needed, so the judgement stands as first written")
    lines.append("")
    lines += _render_audit_checks(audit)
    return lines


def _render_audit_checks(audit: dict[str, Any]) -> list[str]:
    """What the LLM audit examined, pass or fail.

    A verdict on its own is not reviewable, and a passing audit is exactly when
    you most want to know what was actually looked at.
    """
    checks = [c for c in (audit.get("checks") or []) if isinstance(c, dict)]
    if not checks:
        return []
    lines = ["### What the verifier checked", "", "| Check | Verdict | Evidence |", "| --- | --- | --- |"]
    for c in checks:
        evidence = (c.get("evidence") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{c.get('check')}` | {c.get('verdict')} | {evidence} |"
        )
    lines.append("")
    return lines


def render_round_summary(report: dict[str, Any]) -> str:
    """Markdown scorecard for a scored round."""
    season = report.get("season")
    round_number = report.get("round_number")
    lines = [
        f"# Season {season}, round {round_number} — scorecard",
        "",
        f"Scored {report.get('n_scored')} fixtures "
        f"({report.get('n_pending')} not finished, "
        f"{report.get('n_draws_excluded')} draws excluded). "
        f"Scored at {report.get('scored_at')}.",
        "",
        "| Predictor | n | Accuracy | Brier | Log loss |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name in ("agent", "math"):
        metrics = report.get(name) or {}
        if metrics.get("n"):
            lines.append(
                f"| {name} | {metrics['n']} | {metrics['accuracy']:.3f} | "
                f"{metrics['brier']:.4f} | {metrics['log_loss']:.4f} |"
            )
    home_rate = report.get("home_win_rate") or 0.0
    lines += [
        f"| always back the home team | {report.get('n_scored')} | {home_rate:.3f} | — | — |",
        "",
        "Lower is better for Brier and log loss. Predictions were written "
        "before kickoff and scored from a separate command, so they cannot "
        "have been back-fitted.",
        "",
        "## Fixtures",
        "",
        "| Fixture | Actual | Agent | Hit | Model P(home) |",
        "| --- | --- | --- | :-: | ---: |",
    ]
    for row in report.get("fixtures") or []:
        agent_prob = row.get("agent_home_prob")
        math_prob = row.get("math_home_prob")
        if agent_prob is None:
            agent_cell, hit = "—", "—"
        else:
            side = "home" if agent_prob >= 0.5 else "away"
            agent_cell = f"{side} {max(agent_prob, 1 - agent_prob):.2f}"
            hit = "yes" if side == row.get("actual_winner") else "no"
        lines.append(
            f"| {row.get('home_team')} v {row.get('away_team')} "
            f"| {row.get('actual_score')} | {agent_cell} | {hit} "
            f"| {f'{math_prob:.2f}' if isinstance(math_prob, (int, float)) else '—'} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_thinking(ledger: dict[str, Any]) -> str:
    """Markdown of the model's real scratchpad for each LLM step.

    This is the Ollama `message.thinking` channel (or a hosted model's
    reasoning field), not the structured JSON verdict. Empty sections mean the
    provider returned no thinking for that call.
    """
    request = ledger.get("request") or {}
    lines: list[str] = [
        f"# Agent thinking — {ledger.get('run_id') or '?'}",
        "",
        f"- **Model**: {request.get('llm_provider')}/{request.get('llm_model')}",
        f"- **When**: {ledger.get('created_at') or '—'}",
        "",
        "This file is the model's private reasoning channel when available "
        "(Ollama Gemma 4: `message.thinking` with `think=true`). The structured "
        "prediction still lives in `summary.md` / `ledger.json`.",
        "",
    ]
    trace = ledger.get("thinking_trace") or []
    if not trace:
        lines += [
            "_(No thinking captured yet — either the run has not reached an "
            "LLM step, or the provider did not return a thinking channel.)_",
            "",
        ]
        return "\n".join(lines)

    for entry in trace:
        if not isinstance(entry, dict):
            continue
        step = entry.get("step") or "unknown"
        chars = entry.get("chars")
        at = entry.get("at") or "—"
        thinking = (entry.get("thinking") or "").strip()
        lines += [
            f"## {step}",
            "",
            f"_at {at}"
            + (f" · {chars} chars_" if isinstance(chars, int) else "_"),
            "",
        ]
        if thinking:
            lines += [thinking, ""]
        else:
            lines += ["_(no thinking returned for this step)_", ""]
    return "\n".join(lines)
