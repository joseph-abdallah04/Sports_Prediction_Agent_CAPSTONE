---
name: Phase 1 ETL Backfill
overview: "Build the Phase 1 historical backfill pipeline for the mathematical engine: discover all NRL match URLs (2015-2026) from the draw pages, scrape each match-centre JSON payload, and store the raw data in a local data lake, with resumability and validation."
todos:
  - id: scaffold
    content: Scaffold uv project (pyproject.toml, package layout, README)
    status: completed
  - id: http-layer
    content: Build shared HTTP session with rate limiting and retries
    status: completed
  - id: draw-scraper
    content: Build draw scraper to discover match URLs per season/round
    status: completed
  - id: match-scraper
    content: Build match-centre scraper adapted from reference script
    status: completed
  - id: backfill-cli
    content: Build resumable backfill orchestrator CLI with manifest and failure log
    status: completed
  - id: test-validate
    content: Test on one round plus a 2015 match, validate payload structure
    status: completed
  - id: full-backfill
    content: Run full 2015-2026 backfill and report coverage
    status: completed
isProject: false
---

# Phase 1: NRL Historical Backfill (ETL)

## Goal

Build Job A from [mathematical_engine/Overview.md](mathematical_engine/Overview.md): a one-off bulk pipeline that discovers ~2,200 match URLs (2015-2026) and dumps each match's raw JSON into `mathematical_engine/data_lake/raw_historical/`. Feature engineering and modelling are planned after we have real data.

## Verified data sources

- **Draw page** (`nrl.com/draw/?competition=111&round={r}&season={y}`): hydrates `<div id="vue-draw" q-data="...">` containing `fixtures[].matchCentreUrl`, `filterRounds` (per-season round list, including finals), and `filterSeasons`. Confirmed live today.
- **Match centre page**: hydrates `<div id="vue-match-centre" q-data="...">` — same approach as your reference script [NRL_data_scraper.py](mathematical_engine/reference_files/NRL_data_scraper.py), which I'll adapt rather than rewrite.

## Project structure

The one-off backfill (Job A) lives in its own directory, fully separate from the future weekly incremental pipeline (Job B). Logic that both jobs will need — the polite HTTP session and the match-centre JSON extraction — lives in a small shared `nrl_scraping` package so Job B won't duplicate it later.

```
mathematical_engine/
  pyproject.toml                    # uv project (requests, beautifulsoup4)
  README.md                         # how to run the backfill
  nrl_scraping/                     # shared scraping toolkit (used by Job A now, Job B later)
    __init__.py
    http.py                         # session: headers, retries w/ backoff, rate limiting
    match_scraper.py                # fetch one match centre page -> raw JSON dict
  historical_data_backfill_etl/     # Job A: run once, then never again
    __init__.py
    draw_scraper.py                 # enumerate seasons/rounds -> list of match URLs
    backfill.py                     # orchestrator CLI
  data_lake/                        # RAW (untransformed) data only
    raw_historical/{season}/nrl_match_{matchId}.json
    manifests/                      # discovered URLs + failure log
  reference_files/                  # untouched
```

Notes on scope agreed with you:

- The `data_lake/` holds untransformed JSON only. Where transformed/feature data lives will be decided when we plan Phase 2 (transformations) after verifying the raw data is rich enough.
- The weekly incremental pipeline (Job B) will get its own sibling directory (e.g. `incremental_etl/`) when we build it — it will reuse `nrl_scraping/` but have its own round-by-round discovery and a transform-and-append step.

## Key design points

- **Discovery first, then extraction.** `draw_scraper` walks each season, reads `filterRounds` from the season's first draw page to know exactly how many rounds exist (incl. finals weeks), then collects `matchCentreUrl` for fixtures with `matchState == "FullTime"` (skips byes/upcoming). URLs are written to a manifest JSON so discovery doesn't re-run needlessly.
- **Resumable.** Before fetching a match, the orchestrator checks whether `nrl_match_{matchId}.json` already exists (match ID is derivable after fetch, so we key on URL slug in the manifest with a completed flag). Re-running continues where it left off.
- **Polite scraping.** Single shared `requests.Session` with desktop User-Agent, configurable delay between requests (default ~1s), retry with exponential backoff on 5xx/connection errors, and a hard failure log (`manifests/failures.json`) instead of crashing the whole run.
- **CLI.** `uv run python -m historical_data_backfill_etl.backfill --start-season 2015 --end-season 2026` with `--discover-only` and `--limit N` flags for safe test runs.
- **Validation step.** After a small test run (e.g. one round), a quick check confirms each saved file contains the expected keys (`match.stats.groups`, `match.timeline`, `match.homeTeam.players`) so we know older seasons (2015-2017) actually carry the telemetry the Overview assumes — this is the main risk to verify before the full ~2,200-game run.

## Execution order

1. Scaffold the uv project and package layout.
2. Build the shared HTTP layer and draw scraper; test discovery on one season.
3. Build the match scraper (adapted from your reference script) and backfill orchestrator.
4. Test run on a single round, validate payload structure (especially a 2015 match to confirm telemetry-era data quality).
5. Kick off the full 2015-2026 backfill (long-running, ~40-60 min at 1s delay) and report coverage stats.