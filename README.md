# Sports Prediction Agent — Capstone

A university Capstone project: an AI Agent that predicts sporting outcomes
(NRL matches). An LLM Orchestrator calls a tool that runs a mathematically
grounded prediction engine and returns a probability plus SHAP-based
reasoning for the Agent to weigh in its final call.

## Repository structure

| Path | Purpose |
| --- | --- |
| [`mathematical_engine/`](mathematical_engine/README.md) | The deterministic prediction core: data ETL, feature engineering, and the trained/calibrated XGBoost model with SHAP explanations. |
| [`Glossary.md`](Glossary.md) | Plain-English definitions of the ML and data-engineering terms used throughout. |
| [`key_design_decisions.md`](key_design_decisions.md) | Log of architectural crossroads and the reasoning behind each choice. |

## Build status

- **Phase 1 — Data acquisition (ETL backfill):** done. Raw NRL match JSON, 2015–present.
- **Phase 2 — Feature engineering:** done. Leakage-free 49-feature training dataset.
- **Phase 3 — Mathematical core:** done. Optuna-tuned, calibrated XGBoost + SHAP explainer + upcoming-fixture predictor CLI.
- **Phase 4a — Weekly ETL:** done. Scrape new matches, rebuild features, retrain model.
- **Phase 4b — Serving:** planned. FastAPI endpoint for the LLM Agent.

---

## Weekly ETL: run this after each round

After each NRL round finishes, run **one command** to:

1. Discover newly completed matches on nrl.com (skips games you already have)
2. Scrape their raw JSON into the data lake
3. Rebuild the feature store
4. Retrain the production model

### Prerequisites (one-time)

```bash
cd mathematical_engine
uv sync
brew install libomp   # macOS only — required for XGBoost
```

You must have already run the historical backfill (Phase 1) at least once so
`data_lake/raw_historical/` contains match JSON from 2015 onward.

### The weekly command

From the `mathematical_engine/` directory:

```bash
cd mathematical_engine
uv run python -m weekly_incremental_etl.run
```

This scans the **current calendar year** by default (e.g. 2026 during the
2026 season). Takes about 1–2 minutes if new matches were played (~8 scrapes
at 1 req/sec, plus ~30s feature rebuild and ~3s model training).

To target a specific season explicitly:

```bash
uv run python -m weekly_incremental_etl.run --season 2026
```

### When to run it

Run it **once per round**, after all games in that round have finished —
e.g. Monday morning after the weekend's matches. You do not need to run it
before every prediction; run it to **refresh the data and model**, then use
`model.predict` (or the Phase 4 API) whenever you need a prediction.

### What you should see

A successful run ends with a summary like:

```
=== Weekly ETL complete ===
  Season scanned:          2026
  Pending on draw:         8
  Skipped (known URL):     112
  New matches scraped:     8
  ...
  Training rows:           2330
  Model retrained at:      2026-...
```

- **New matches scraped: 0** — no new games since your last run (safe to ignore; model still rebuilds/retrains).
- **New matches scraped: 8** — eight new results were added and the model was updated.

### Useful flags

| Command | When to use |
| --- | --- |
| `--dry-run` | Preview which matches would be scraped, without changing anything |
| `--scrape-only` | Scrape new JSON only (skip rebuild/retrain) — debugging |
| `--skip-scrape` | Rebuild features + retrain only (raw data already updated) |

```bash
uv run python -m weekly_incremental_etl.run --dry-run
```

### Verify it worked

```bash
# Check training row count increased (if new matches were scraped)
cat models/metrics.json

# Predict an upcoming fixture with the refreshed model
uv run python -m model.predict \
  --home Broncos --away Storm \
  --venue "Suncorp Stadium" \
  --date 2026-07-04T09:30:00Z
```

### Important notes

- **Always run from `mathematical_engine/`**, not from `models/` or the repo root.
- **No duplicates:** matches already on disk are skipped automatically.
- **No hyperparameter tuning:** weekly runs reuse `models/best_params.json`. Re-tune manually with `uv run python -m model.tune` only off-season or after major feature changes.
- **Logs:** scrape failures go to `data_lake/manifests/weekly_failures.json`; last run summary in `data_lake/manifests/weekly_last_run.json`.

---

## Further reading

- [`mathematical_engine/README.md`](mathematical_engine/README.md) — full engine layout, backfill, feature engineering, model training.
- [`mathematical_engine/Overview.md`](mathematical_engine/Overview.md) — system architecture and rationale.
- [`plans/phase_4a_weekly_etl.plan.md`](plans/phase_4a_weekly_etl.plan.md) — weekly ETL design document.
