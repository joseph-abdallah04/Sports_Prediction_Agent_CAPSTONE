# Mathematical Engine

The deterministic prediction core of the Sports Prediction Agent. See
[Overview.md](Overview.md) for the full architecture rationale.

## Layout

| Path | Purpose |
| --- | --- |
| `nrl_scraping/` | Shared scraping toolkit (HTTP session, match-centre extractor). Used by both ETL jobs. |
| `historical_data_backfill_etl/` | Job A: one-off backfill of all raw match data, 2015-present. Run once. |
| `data_lake/` | Raw, untransformed match JSON only. |
| `feature_engineering/` | Phase 2: flattens raw JSON and builds the leakage-free training dataset. |
| `feature_store/` | Transformed Parquet output (`matches_flat.parquet`, `training_dataset.parquet`). |
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
