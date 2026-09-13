# Running the old and the new system side by side

The recalibration changed how the agent judges. To compare the two fairly we
keep **both versions runnable** and predict the same upcoming fixture with each.

The old system is not a reconstruction. It is the exact commit that produced
Rounds 23-25, checked out as a second working copy.

| | Old system | New system |
|---|---|---|
| Commit | `dccb09c` (`final predictions for round 25`, 23 Aug 2026) | current `main` |
| Working copy | `legacy/` (git worktree, detached HEAD) | repo root |
| Run output | `legacy/agent_runs/` | [`agent_runs/`](../../agent_runs/) |
| Official rounds already in its log | 23, 24, 25 (24 rows) | 26 onwards (new-system log). Side-by-side comparison starts Finals Week 1 (round 28) |
| Confidence ceiling in code | 0.95 | 0.85 |
| Judgement rules | pre-recalibration prompts and verifier | [`EXPECTED_BEHAVIOUR.md`](EXPECTED_BEHAVIOUR.md) |

The recalibration landed in `878f4cc`, then `4486085` and `7b9b832`. Everything
before `dccb09c` is untouched by it. See [`SYSTEM_RECALIBRATION.md`](SYSTEM_RECALIBRATION.md)
for what changed and [`FINDINGS_AFTER_ROUND25.md`](FINDINGS_AFTER_ROUND25.md) for why.

## What the two trees share

Both use the **same trained XGBoost model and the same match data**, so a
difference in output is a difference in judgement, not in training data. Three
symlinks inside the worktree point back at the live engine:

```
legacy/tools/mathematical_engine/models        -> ../../../tools/mathematical_engine/models
legacy/tools/mathematical_engine/data_lake     -> ../../../tools/mathematical_engine/data_lake
legacy/tools/mathematical_engine/feature_store -> ../../../tools/mathematical_engine/feature_store
legacy/agent/.env                              -> ../../agent/.env
```

Run the weekly ETL from the main tree only. The worktree picks up the retrained
model automatically.

The old tree still has its **own** copies of the prompts, verifier, research
filter, and `explain.py`, which is the whole point. In particular it keeps the
pre-recalibration `explain.py`, so it does not emit the `Too close` label.

## Predicting a fixture with both

One CLI process at a time. Confirm nothing is running first:

```bash
pgrep -f agent_app.cli    # expect no output
```

New system:

```bash
cd agent
uv run python -m agent_app.cli --home TEAM --away TEAM --round N --force-refresh -v
```

Old system, only after the new run has fully exited:

```bash
cd legacy/agent
uv run python -m agent_app.cli --home TEAM --away TEAM --round N --force-refresh -v
```

Roughly 8-12 minutes each on local Ollama, so budget ~25 minutes per fixture for
the pair. Start well before kickoff. Pick one order (new first, or old first) and
keep it for every fixture, so neither system systematically gets fresher news.

Wests Tigers needs the full name: `--away "Wests Tigers"`.

## Keeping the results apart

The two logs must never be merged. Each tree resolves `agent_runs_dir` from its
own repo root, so this happens by itself:

- New rows append to `agent_runs/predictions_log.csv`
- Old rows append to `legacy/agent_runs/predictions_log.csv`

`legacy/` is git-ignored, so old-system output is never committed to `main`.
Copy it out by hand if you want it in the report.

When writing up a run, always say which tree produced the pick. Hold the new run
against [`EXPECTED_BEHAVIOUR.md`](EXPECTED_BEHAVIOUR.md); the old run is not held
to that file, because that file *is* the new logic.

## Setting the worktree up again

If `legacy/` is ever deleted:

```bash
git worktree add --detach legacy dccb09c
cd legacy/tools/mathematical_engine
ln -sfn ../../../tools/mathematical_engine/models models
ln -sfn ../../../tools/mathematical_engine/data_lake data_lake
ln -sfn ../../../tools/mathematical_engine/feature_store feature_store
cd ../../agent && ln -sfn ../../agent/.env .env && uv sync
```

Check it came up correctly:

```bash
uv run python -m agent_app.cli --show-config   # runs dir must end in legacy/agent_runs
uv run python scripts/smoke_orchestrator.py    # offline, ~2s, prints SMOKE_OK
```

The old smoke reports `confidence_above_ceiling:0.99>0.95`. The new tree reports
`>0.85`. That difference is a quick way to confirm you are in the tree you think
you are in.
