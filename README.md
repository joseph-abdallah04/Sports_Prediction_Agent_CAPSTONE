# Sports Prediction Agent — Capstone

A university Capstone project: an AI Agent that predicts sporting outcomes
(NRL matches). An LLM Orchestrator calls a tool that runs a mathematically
grounded prediction engine and returns a probability plus SHAP-based
reasoning for the Agent to weigh in its final call.

## Repository structure

| Path | Purpose |
| --- | --- |
| [`tools/`](tools/README.md) | Fact tools (math, scene, research) + MCP gateway. |
| [`tools/mathematical_engine/`](tools/mathematical_engine/README.md) | The deterministic prediction core: data ETL, feature engineering, and the trained/calibrated XGBoost model with SHAP explanations (CLI). |
| [`tools/qualitative_research/`](tools/qualitative_research/README.md) | Facts-only multi-channel research tool (nrl.com, DDG, Google News RSS, Reddit) with CLI. |
| [`tools/fixture_scene/`](tools/fixture_scene/README.md) | First-pipeline scene setter: nrl.com draw/match centre + Open-Meteo weather (CLI). |
| [`tools/mcp_gateway/`](tools/mcp_gateway/README.md) | MCP server exposing scene / research / math tools to an agent client. |
| [`agent/`](agent/README.md) | Constrained-pipeline LLM Orchestrator (query plan, judgement, verifier loops, ledger). |
| [`Glossary.md`](Glossary.md) | Plain-English definitions of the ML and data-engineering terms used throughout. |
| [`key_design_decisions.md`](key_design_decisions.md) | Log of architectural crossroads and the reasoning behind each choice. |

## Build status

- **Phase 1 — Data acquisition (ETL backfill):** done. Raw NRL match JSON, 2015–present.
- **Phase 2 — Feature engineering:** done. Leakage-free 49-feature training dataset.
- **Phase 3 — Mathematical core:** done. Optuna-tuned, calibrated XGBoost + SHAP explainer + upcoming-fixture predictor CLI.
- **Phase 4a — Weekly ETL:** done. Scrape new matches, rebuild features, retrain model.
- **Phase 4b — Serving:** superseded. Shared `predict_fixture()` remains; agent access is via MCP (see `tools/mcp_gateway/`), not per-tool FastAPI.
- **Module 1 — Qualitative research:** done. CLI + MCP tool `research_fixture_news`.
- **Module — Fixture scene:** done. CLI + MCP tool `set_fixture_scene`.
- **MCP gateway:** done. One stdio MCP server for all fact tools.
- **Agent Orchestrator:** done. Scene → research queries → predict → judgement → verifier (see `agent/`).

---

## Before you run anything

All commands below are run from the **`tools/mathematical_engine/`** directory —
not the repo root, and not from `models/` inside it.

```bash
cd tools/mathematical_engine
```

### One-time setup (new machine or fresh clone)

| Command | When | Why |
| --- | --- | --- |
| `uv sync` | First time, or after pulling dependency changes | Installs Python packages (`xgboost`, `optuna`, `shap`, etc.) |
| `brew install libomp` | Once on macOS | XGBoost needs the OpenMP runtime on Mac |

```bash
cd tools/mathematical_engine
uv sync
brew install libomp   # macOS only
```

You also need the historical raw data lake from the one-off backfill (Phase 1).
If `data_lake/raw_historical/` is empty, run the backfill command in the
[one-time section](#one-time--rare) below first.

---

## Standard weekly workflow

During the NRL season, this is all you normally need:

```bash
cd tools/mathematical_engine

# 1. After each round finishes (e.g. Monday morning)
uv run python -m weekly_incremental_etl.run

# 2. Whenever you want a prediction for an upcoming game
uv run python -m model.predict \
  --home Broncos \
  --away Storm \
  --venue "Suncorp Stadium" \
  --date 2026-07-04T09:30:00Z
```

Step 1 scrapes new results, rebuilds features, and **fully replaces**
`models/model.ubj` (your trained model). Step 2 uses that fresh model
immediately — no separate train step required.

---

## Command reference

### Every week (during the season)

#### `weekly_incremental_etl.run` — scrape + rebuild + retrain

**When:** Once per round, after all games in that round have finished.

**Why:** Keeps raw data, features, and the production model up to date with
the latest results. This is Job B — the main pipeline you run weekly.

```bash
uv run python -m weekly_incremental_etl.run
```

Scans the **current calendar year** by default. Takes ~1–2 minutes when new
matches exist (~8 scrapes at 1 req/sec + ~30s feature rebuild + ~3s train).

| Flag | When to use |
| --- | --- |
| `--season 2026` | Explicitly target a season (e.g. catch-up at season start) |
| `--dry-run` | Preview which matches would be scraped — no writes |
| `--scrape-only` | Scrape new JSON only; skip rebuild and retrain (debugging) |
| `--skip-scrape` | Rebuild features + retrain only; raw data already updated |

```bash
uv run python -m weekly_incremental_etl.run --season 2026
uv run python -m weekly_incremental_etl.run --dry-run
```

**What it updates:**

| Output | Location |
| --- | --- |
| New raw match JSON | `data_lake/raw_historical/{season}/nrl_match_*.json` |
| Feature tables | `feature_store/matches_flat.parquet`, `training_dataset.parquet` |
| Production model | `models/model.ubj`, `calibrator.pkl`, `metrics.json`, etc. |
| Run summary | `data_lake/manifests/weekly_last_run.json` |

**What it does NOT update:** `reports/` (see `model.evaluate` below).

**Duplicates:** Matches already on disk are skipped automatically. Safe to
re-run; you'll see `New matches scraped: 0` if nothing new played.

---

### When you need a prediction

#### `model.predict` — predict an upcoming fixture

**When:** Any time you want a probability + SHAP reasoning for a game that
hasn't been played yet — after the weekly ETL has run.

**Why:** This is the end product of the mathematical engine: the JSON payload
the LLM Agent will consume (via the Phase 4b API later).

```bash
uv run python -m model.predict \
  --home Sharks \
  --away Eels \
  --venue "PointsBet Stadium" \
  --date 2026-07-04T09:30:00Z \
  --weather Rain
```

| Argument | Required | Notes |
| --- | --- | --- |
| `--home` | Yes | Team nickname, e.g. `Broncos` |
| `--away` | Yes | Team nickname, e.g. `Storm` |
| `--venue` | Yes | Exact venue name, e.g. `"Suncorp Stadium"` |
| `--date` | Yes | Kickoff datetime, ISO format |
| `--weather` | No | `Fine`, `Rain`, etc. Defaults to `unknown` |
| `--top-k` | No | Number of SHAP drivers per direction (default 5) |

---

### Occasionally (not every week)

#### `model.evaluate` — holdout metrics and report plots

**When:** Before a supervisor meeting, capstone write-up, or whenever you
want refreshed performance numbers. **Not** required for predictions.

**Why:** Produces an honest backtest on untouched 2025–2026 data (AUC,
accuracy, log loss) plus charts for your report. The weekly ETL does not
run this automatically.

```bash
uv run python -m model.evaluate
```

**Writes to `reports/`:**

| File | Contents |
| --- | --- |
| `holdout_metrics.json` | AUC, accuracy, log loss vs baselines |
| `calibration_curve.png` | Probability reliability diagram |
| `shap_summary.png` | Global feature importance chart |

---

#### `model.tune` — hyperparameter search

**When:** Off-season, or after significant feature/dataset changes. **Not**
part of the weekly loop.

**Why:** Optuna searches for better XGBoost settings (~200 trials, ~95s).
Saves winners to `models/best_params.json`. Weekly ETL reuses these params;
it does not re-tune.

```bash
uv run python -m model.tune
uv run python -m model.tune --trials 50   # quicker test run
```

After tuning, retrain manually or let the next weekly ETL pick up the new
params:

```bash
uv run python -m model.train
```

---

### One-time / rare

#### `historical_data_backfill_etl.backfill` — full historical scrape (Job A)

**When:** Once, to build the initial raw data lake (2015–present). Also if
rebuilding from scratch on a new machine.

**Why:** Discovers and scrapes ~2,200+ matches into `data_lake/raw_historical/`.
Resumable via `data_lake/manifests/backfill_manifest.json`.

```bash
# Full run (~1 hour at 1 req/sec)
uv run python -m historical_data_backfill_etl.backfill

# Discover URLs only (safe test)
uv run python -m historical_data_backfill_etl.backfill --discover-only --start-season 2026 --end-season 2026

# Scrape a handful of matches (test)
uv run python -m historical_data_backfill_etl.backfill --limit 5
```

After backfill, validate the lake:

```bash
uv run python -m historical_data_backfill_etl.validate
```

---

#### `feature_engineering.build_dataset` — rebuild features manually

**When:** Rarely needed — the weekly ETL does this automatically. Use if you
edited feature code or raw JSON by hand and want to rebuild without scraping.

**Why:** Runs Stage 1 (flatten JSON → `matches_flat.parquet`) and Stage 2
(ratings, form, context → `training_dataset.parquet`).

```bash
uv run python -m feature_engineering.build_dataset
uv run python -m feature_engineering.build_dataset --reflatten   # force re-read all JSON
```

---

#### `model.train` — retrain without scraping

**When:** Rarely needed — the weekly ETL does this automatically. Use after
manual `build_dataset`, after `model.tune`, or if you only want to retrain.

**Why:** Fits the production XGBoost on all data and overwrites `models/`
(including `model.ubj`).

```bash
uv run python -m model.train
```

---

### Debugging and development

#### `weekly_incremental_etl.run --dry-run`

**When:** Before a weekly run, to see what would be scraped.

**Why:** Lists pending matches without downloading or retraining.

```bash
uv run python -m weekly_incremental_etl.run --dry-run
```

---

#### `feature_engineering.inference` — train/inference parity test

**When:** After changing feature engineering code. Not a routine operator command.

**Why:** Verifies that features built for upcoming fixtures match the stored
training dataset for historical games (guards against train/serve skew).

```bash
uv run python -m feature_engineering.inference
```

Expect: `PARITY TEST PASSED`.

---

#### `feature_engineering.smoke_test` — quick dataset sanity check

**When:** After major feature pipeline changes. Not routine.

**Why:** Trains a basic XGBoost on a chronological split and reports AUC.
Flags leakage (AUC suspiciously high) or broken features (AUC near random).

```bash
uv run python -m feature_engineering.smoke_test
```

---

#### `feature_engineering.flatten` — Stage 1 only

**When:** Development/debugging of the flattening logic only.

**Why:** Converts raw JSON to `matches_flat.parquet` without computing
pre-match features. Normally called by `build_dataset` or the weekly ETL.

```bash
uv run python -m feature_engineering.flatten
```

---

### Agent tool access (MCP)

Per-tool FastAPI servers were removed. The agent (and any MCP host) talks to
one gateway that calls the same library functions as the CLIs.

```bash
cd tools/mcp_gateway
uv sync
uv run python -m gateway
```

| MCP tool | Backing package |
| --- | --- |
| `set_fixture_scene` | `fixture_scene` |
| `research_fixture_news` | `qualitative_research` |
| `predict_match` | `mathematical_engine` |
| `tools_health` | gateway |

Human debugging stays on CLIs (`scene.cli`, `research.cli`, `model.predict`).
Design: [`tools/mcp_gateway/Architecture.md`](tools/mcp_gateway/Architecture.md).

Smoke (no MCP host required):

```bash
cd tools/mcp_gateway && uv run python scripts/smoke_tools.py
```

---

### Prediction agent (Orchestrator)

Constrained pipeline over the same fact tools (in-process; MCP remains available
for other hosts). Design: [`agent/Architecture.md`](agent/Architecture.md) ·
ADRs: [`agent/adrs/`](agent/adrs/).

```bash
cd agent
uv sync
cp .env.example .env   # LLM_PROVIDER=ollama, LLM_MODEL=gemma4:31b, …

uv run python -m agent_app.cli --home Eels --away Panthers
```

Writes `agent_runs/<run_id>/ledger.json`. Loops: research refine ≤1; verifier
recalibrate ≤1 (same judgement session, no new tools).

---

## Quick reference table

| Command | Frequency | Purpose |
| --- | --- | --- |
| `weekly_incremental_etl.run` | **Weekly** | Scrape new games + rebuild features + retrain model |
| `python -m gateway` (in `tools/mcp_gateway/`) | **When exposing tools via MCP** | MCP server for fact tools |
| `python -m agent_app.cli` (in `agent/`) | **When running a full prediction** | Orchestrator + ledger |
| `model.predict` | **As needed** | Get prediction JSON for an upcoming fixture (CLI) |
| `model.evaluate` | Occasional | Refresh holdout metrics and `reports/` plots |
| `model.tune` | Rare | Search for better hyperparameters |
| `model.train` | Rare* | Retrain model only (*weekly ETL does this) |
| `historical_data_backfill_etl.backfill` | Once | Build initial raw data lake |
| `historical_data_backfill_etl.validate` | After backfill | Check raw data quality |
| `feature_engineering.build_dataset` | Rare* | Rebuild features only (*weekly ETL does this) |
| `feature_engineering.inference` | Dev only | Parity test |
| `feature_engineering.smoke_test` | Dev only | Dataset learnability check |
| `uv sync` | Setup | Install dependencies |

### Official NRL nickNames (use these in CLI flags)

Pass **exactly** the nickName column below to `--home` / `--away` (case-insensitive).
The scene tool matches them to nrl.com draw data — each Premiership club has a
unique nickName, so `Titans` is always the Gold Coast Titans (there is no
`Gold Coast` flag and you should not type the full club name).

| Club | nickName to type |
| --- | --- |
| Brisbane Broncos | `Broncos` |
| Canberra Raiders | `Raiders` |
| Canterbury-Bankstown Bulldogs | `Bulldogs` |
| Cronulla-Sutherland Sharks | `Sharks` |
| Dolphins | `Dolphins` |
| Gold Coast Titans | `Titans` |
| Manly Warringah Sea Eagles | `Sea Eagles` |
| Melbourne Storm | `Storm` |
| Newcastle Knights | `Knights` |
| North Queensland Cowboys | `Cowboys` |
| Parramatta Eels | `Eels` |
| Penrith Panthers | `Panthers` |
| South Sydney Rabbitohs | `Rabbitohs` |
| St. George Illawarra Dragons | `Dragons` |
| Sydney Roosters | `Roosters` |
| New Zealand Warriors | `Warriors` |
| Wests Tigers | `Wests Tigers` |

Home team is first (left) on the nrl.com match card. For Thursday’s Titans vs
Cowboys at Cbus Super Stadium:

```bash
cd agent
uv run python -m agent_app.cli --home Titans --away Cowboys
```

---

## Verify a weekly run worked

```bash
# Training row count and timestamp (should increase after new rounds)
cat models/metrics.json

# Last weekly ETL summary
cat data_lake/manifests/weekly_last_run.json

# Scrape failures (should be empty)
cat data_lake/manifests/weekly_failures.json

# Test prediction with refreshed model
uv run python -m model.predict \
  --home Broncos --away Storm \
  --venue "Suncorp Stadium" \
  --date 2026-07-04T09:30:00Z
```

---

## Qualitative research tool

Facts-only multi-channel research for an upcoming fixture (no LLM). Run from
`tools/qualitative_research/`:

```bash
cd tools/qualitative_research
uv sync

uv run python -m research.cli \
  --home Eels --away Panthers \
  --kickoff 2026-07-25T19:30:00+10:00 --round 21

# Agent access: via mcp_gateway tool research_fixture_news
```

See [`tools/qualitative_research/README.md`](tools/qualitative_research/README.md) and
[`tools/qualitative_research/Architecture.md`](tools/qualitative_research/Architecture.md).

---

## Fixture scene tool

Compulsory first tool: resolve an upcoming fixture from nrl.com and attach
Open-Meteo kickoff weather. Run from `tools/fixture_scene/`:

```bash
cd tools/fixture_scene
uv sync

uv run python -m scene.cli --home Eels --away Panthers

# Agent access: via mcp_gateway tool set_fixture_scene
```

See [`tools/fixture_scene/README.md`](tools/fixture_scene/README.md) and
[`tools/fixture_scene/Architecture.md`](tools/fixture_scene/Architecture.md).

---

## Important notes

- **Working directory:** always `tools/mathematical_engine/` for math `uv run python -m ...`; use `tools/qualitative_research/` for research; use `tools/fixture_scene/` for scene; use `tools/mcp_gateway/` for the MCP server; use `agent/` for the Orchestrator.
- **No duplicates:** weekly ETL skips matches already in the data lake.
- **Model replacement:** each weekly run fully overwrites `models/model.ubj`.
- **No tuning weekly:** hyperparameters come from `models/best_params.json`.
- **Reports are separate:** run `model.evaluate` when you want updated charts/metrics.

---

## Further reading

- [`agent/Architecture.md`](agent/Architecture.md) — Orchestrator control loop and agency.
- [`tools/mathematical_engine/README.md`](tools/mathematical_engine/README.md) — engine layout and technical detail.
- [`tools/mathematical_engine/Overview.md`](tools/mathematical_engine/Overview.md) — system architecture.
- [`tools/mathematical_engine/model/Architecture.md`](tools/mathematical_engine/model/Architecture.md) — model training and evaluation design.
- [`tools/qualitative_research/Architecture.md`](tools/qualitative_research/Architecture.md) — research channels, filters, ledger contract.
- [`tools/fixture_scene/Architecture.md`](tools/fixture_scene/Architecture.md) — scene tool Orchestrator contract and sources.
- [`tools/mcp_gateway/Architecture.md`](tools/mcp_gateway/Architecture.md) — MCP tool gateway (agent integration).
- [`plans/math_engine_plans/phase_4a_weekly_etl.plan.md`](plans/math_engine_plans/phase_4a_weekly_etl.plan.md) — weekly ETL design document.
- [`Glossary.md`](Glossary.md) — definitions for AUC, log loss, SHAP, etc.
