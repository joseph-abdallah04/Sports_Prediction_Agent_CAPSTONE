# Mathematical Engine

The deterministic prediction core of the Sports Prediction Agent. See
[Overview.md](Overview.md) for the full architecture rationale.

**Operator commands (when/why for every command):** see the project root
[README.md](../../README.md#command-reference).

## Layout

| Path | Purpose |
| --- | --- |
| `nrl_scraping/` | Shared scraping toolkit (HTTP session, match-centre extractor). Used by both ETL jobs. |
| `historical_data_backfill_etl/` | Job A: one-off backfill of all raw match data, 2015-present. Run once. |
| `weekly_incremental_etl/` | Job B: weekly pipeline — scrape new matches, rebuild features, retrain model. |
| `data_lake/` | Raw, untransformed match JSON only. |
| `feature_engineering/` | Phase 2: flattens raw JSON and builds the leakage-free training dataset. Also `inference.py` (Phase 3): builds features for upcoming fixtures. |
| `feature_store/` | Transformed Parquet output (`matches_flat.parquet`, `training_dataset.parquet`). |
| `model/` | Phase 3: tune, train, calibrate, evaluate, explain, and predict. Also `serving.py`: shared prediction layer used by the CLI and MCP `predict_match`. |
| `models/` | Trained artifacts (gitignored): `model.ubj`, `calibrator.pkl`, `best_params.json`, `feature_columns.json`, `metrics.json`. |
| `reports/` | Evaluation outputs: calibration curve, SHAP summary, holdout metrics. |
| `reference_files/` | Original prototype scripts and a sample payload. Not source code. |

See [Feature_Dictionary.md](Feature_Dictionary.md) for every feature in the
training dataset and [Data_Quality_Findings.md](Data_Quality_Findings.md)
for raw-data caveats.

## Setup

Requires [uv](https://docs.astral.sh/uv/). From `mathematical_engine/`:

```bash
uv sync
```

## Job A: Historical Backfill

Discovers every completed NRL Premiership match from the nrl.com draw
pages, scrapes each match centre's embedded JSON payload, and stores it
untouched in `data_lake/raw_historical/{season}/nrl_match_{matchId}.json`.

```bash
# Full run (2015-2026, ~2,200 matches, roughly an hour at 1 req/sec)
uv run python -m historical_data_backfill_etl.backfill

# Safe test run: discover URLs only
uv run python -m historical_data_backfill_etl.backfill --discover-only --start-season 2025 --end-season 2025

# Scrape just a handful of matches
uv run python -m historical_data_backfill_etl.backfill --limit 5
```

The run is **resumable**: progress is checkpointed to
`data_lake/manifests/backfill_manifest.json`, so re-running after an
interruption continues where it left off. Failures are logged to
`data_lake/manifests/failures.json` without stopping the run.

After a run, validate the data lake:

```bash
uv run python -m historical_data_backfill_etl.validate
```

This reports per-season file counts and flags any matches missing the
structures Phase 2 feature engineering depends on (`stats.groups`,
`timeline`, player stats, scores).

## Phase 2: Feature Engineering

Requires the OpenMP runtime for XGBoost on macOS: `brew install libomp`.

```bash
# Stage 1 only: flatten raw JSON into per-match facts
uv run python -m feature_engineering.flatten

# Stages 1+2: build the model-ready training dataset (prints feature coverage)
uv run python -m feature_engineering.build_dataset

# Sanity-check the dataset with a quick chronological-split XGBoost run
uv run python -m feature_engineering.smoke_test
```

Outputs land in `feature_store/`. Draws and phantom COVID games are
excluded; era-missing telemetry stays NaN (never imputed). Unknown venues
print a warning and should be added to `VENUE_TO_STATE` in
`feature_engineering/flatten.py`.

## Phase 3: The Mathematical Core (model + SHAP + predictor)

A tuned, probability-calibrated XGBoost classifier with a SHAP explainer and
a CLI that predicts upcoming fixtures. Full design rationale in
[model/Architecture.md](model/Architecture.md).

```bash
# Occasional: Optuna hyperparameter search -> models/best_params.json (~95s)
uv run python -m model.tune

# Weekly: fit + calibrate the production model -> models/ (seconds)
uv run python -m model.train

# Honest backtest on the untouched 2025-2026 holdout, + plots -> reports/
uv run python -m model.evaluate

# Prove train/inference feature consistency
uv run python -m feature_engineering.inference

# Predict an upcoming fixture (prints the Overview-format JSON payload)
uv run python -m model.predict --home Broncos --away Storm \
    --venue "Suncorp Stadium" --date 2026-07-04T09:30:00Z
```

The tuning/training split is deliberate: hyperparameters track the dataset's
shape (re-tune occasionally), while training reuses the saved params and is
fast enough to re-run every round. Validation uses expanding-window
chronological folds with 2025-2026 held out, so reported metrics (holdout
AUC ~0.64, accuracy ~63% vs 56% always-home baseline) reflect genuine future
performance. The MCP gateway and the weekly ETL job build on these artifacts in
Phase 4.

## Job B: Weekly incremental ETL

Run once after each NRL round completes to pull new results, refresh the
feature store, and retrain the model. See the project root
[README.md](../../README.md#weekly-etl-run-this-after-each-round) for the
operator runbook.

```bash
uv run python -m weekly_incremental_etl.run              # default: current season
uv run python -m weekly_incremental_etl.run --season 2026
uv run python -m weekly_incremental_etl.run --dry-run    # preview pending scrapes
```

## Agent serving (via MCP)

Prediction for the agent is exposed through
[`mcp_gateway`](../mcp_gateway/README.md) tool `predict_match`, which calls
the same `predict_fixture()` as the CLI. Artifacts hot-reload when
`models/metrics.json` changes (e.g. after weekly ETL).

```bash
# CLI (human / demo)
uv run python -m model.predict \
  --home Broncos --away Storm \
  --venue "Suncorp Stadium" \
  --date 2026-07-04T09:30:00Z

# Agent: cd ../mcp_gateway && uv run python -m gateway
```
