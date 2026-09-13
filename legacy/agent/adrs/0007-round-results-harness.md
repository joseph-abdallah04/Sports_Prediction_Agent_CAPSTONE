# ADR 0007: Whole-round results harness

## Status

Accepted. Indexed as DD-32 in `key_design_decisions.md`.

## Context

Until now the agent was exercised one fixture at a time, by hand, and never
scored against what actually happened. That makes every claim about it
anecdotal: a single correct pick says nothing, and there was no way to answer
the only question that matters for the report — is the agent better than the
math model alone, and is either better than backing the home side every week?

## Decision

`agent_app.harness` provides two commands that must be run at different times:

```bash
# before the round
uv run python -m agent_app.harness run --season 2026 --round 23

# after the last game
uv run python -m agent_app.harness score --season 2026 --round 23
```

`run` reads every Premiership fixture in the round from the nrl.com draw
(`scene.draw.list_round_fixtures`), runs the full agent on each, and writes the
predictions to `agent_runs/rounds/<season>R<round>.json`.

`score` reads that file back, pulls final scores from the same draw pages
(`scene.draw.fixture_result`), and reports accuracy, Brier score and log loss
for three predictors: the agent, the raw math model, and always-back-the-home-
team. Draws are excluded and counted; unfinished matches are reported as
pending rather than scored.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Score from the agent's own ledgers on demand | Ledgers hold predictions, not results, and re-deriving the fixture list each time invites mismatches |
| Take results from the math engine's data lake | Requires the weekly ETL to have run first; the draw page has the score minutes after full time |
| Let the operator pass an explicit fixture list | Hand-picking fixtures is how you accidentally report your best ones |
| Backtest the agent over historical rounds | Research channels return *today's* news; there is no way to reconstruct what was knowable before a 2023 kickoff, so historical agent backtests would be leak-ridden fiction |

## Consequences

Predictions are written to disk before kickoff and scoring reads that file, so
results cannot be back-fitted — the separation is the point, not a convenience.

The math model can be backtested honestly over years (`model.evaluate`), but
the agent can only be measured forward, one round at a time. Round 23 of 2026
is therefore the first data point, and any comparison of agent versus model
will stay small-sample for the rest of the season. The harness reports `n`
alongside every metric so that limitation is visible rather than implied.
