# Mathematical Engine

The deterministic prediction core of the Sports Prediction Agent. See
[Overview.md](Overview.md) for the full architecture rationale.

## Layout

| Path | Purpose |
| --- | --- |
| `nrl_scraping/` | Shared scraping toolkit (HTTP session, match-centre extractor). Used by both ETL jobs. |
| `historical_data_backfill_etl/` | Job A: one-off backfill of all raw match data, 2015-present. Run once. |
| `data_lake/` | Raw, untransformed match JSON only. Transformed/feature data lives elsewhere (Phase 2). |
| `reference_files/` | Original prototype scripts and a sample payload. Not source code. |

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
