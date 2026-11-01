# NRL Prediction Agent

A university Capstone project that forecasts NRL match winners before kickoff.

A local AI model (Gemma 4, run through Ollama) reads this week's match news and
adjusts a home-win probability from a statistical model (XGBoost). A fixed
pipeline controls each step, a verification step checks the result, and every
run is saved in full.

## How a forecast works

1. **Fixture scene:** gets the venue, kickoff, officials and weather.
2. **Search queries:** Gemma 4 writes searches for this match.
3. **Research and model:** the research tool gathers news while XGBoost gives
   the home-win probability and the reasons behind it.
4. **Research gate:** checks the articles are about this match, and allows one
   retry if they aren't.
5. **Judgement:** Gemma 4 picks a winner and a confidence.
6. **Verification:** a coded checklist and a separate audit check the judgement.
7. **Revision:** the judgement is revised once if needed.
8. **Run record:** the forecast and all its evidence are saved.

## Repository layout

| Path | What it holds |
| --- | --- |
| `agent/` | The new system's pipeline, prompts and verifier |
| `tools/fixture_scene/` | Fixture, venue and weather tool |
| `tools/qualitative_research/` | News research tool (nrl.com, DuckDuckGo, Google News RSS) |
| `tools/mathematical_engine/` | Match data, features, XGBoost model and weekly update |
| `agent_runs/` | The new system's forecasts |
| `legacy/` | The old system, with its own code and forecasts |
| `Reporting/` | Analysis script, results workbook and outputs |
| `config.toml` | Choice of AI model, timeouts and loop limits |

### Code quoted in the report

| Report | File |
| --- | --- |
| Appendix C, new judge prompt | `agent/src/agent_app/prompts/__init__.py` (`JUDGEMENT_SYSTEM`) |
| Old judge prompt | `legacy/agent/src/agent_app/prompts/__init__.py` |
| Appendix D, old checklist | `legacy/agent/src/agent_app/verifier.py` |
| Appendix E, new checklist | `agent/src/agent_app/verifier.py` |
| Appendix F, confidence bands | `agent/src/agent_app/prompts/__init__.py`, lines 177–189 |

## Two systems

The system was revised after Round 25, so two versions are kept.

| | Old system | New system |
| --- | --- | --- |
| Code | `legacy/` | `agent/` and `tools/` |
| Rounds forecast | 23–25 and all finals | 26–27 and all finals |
| Run records | `legacy/agent_runs/fixtures/` | `agent_runs/fixtures/` |
| Run log | `legacy/agent_runs/predictions_log.csv` | `agent_runs/predictions_log.csv` |

Both systems share one trained model and one set of match data. Links inside
`legacy/tools/mathematical_engine/` point to the main copies.

## Setup

You need [uv](https://docs.astral.sh/uv/), Python 3.12 or later, and
[Ollama](https://ollama.com/). The default model is built for Apple Silicon.

```bash
ollama pull gemma4:31b-mlx
brew install libomp              # macOS only, needed by XGBoost

cd agent && uv sync              # new system
cd ../legacy/agent && uv sync    # old system
```

The trained model is included, so no training is needed before a forecast. API
keys are only needed for a hosted AI model: copy `agent/.env.example` to
`agent/.env`, then change `provider` in `config.toml`.

## Run a forecast

Start Ollama with `ollama serve`, then run:

```bash
cd agent
uv run python -m agent_app.cli --home Titans --away Cowboys --round 23 --force-refresh
```

Use `legacy/agent` instead of `agent` to run the old system. Run one forecast at
a time. Each takes about 10–20 minutes on a local model.

Use the home team first and these team names: Broncos, Bulldogs, Cowboys,
Dolphins, Dragons, Eels, Knights, Panthers, Rabbitohs, Raiders, Roosters,
Sea Eagles, Sharks, Storm, Titans, Warriors, Wests Tigers. Put quotes around
two-word names, such as `--away "Wests Tigers"`.

To see the settings in use: `uv run python -m agent_app.cli --show-config`

## Read a run

Each run folder holds four files, and each forecast adds a row to that system's
`predictions_log.csv`.

| File | What it holds |
| --- | --- |
| `summary.md` | The forecast and reasoning in plain text. Start here. |
| `thinking.md` | The model's working notes |
| `record.json` | The run's key numbers |
| `ledger.json` | The full record of every tool call and response |

The folder `20260806T005157Z - OLD TEST` and the run `20260919T022217Z` in
`2026-R29_Roosters-v-Sharks` were not scored. The run log in `agent_runs/` also
repeats the old system's Round 23–25 rows.

## Update the match data

XGBoost and the data pipeline live in `tools/mathematical_engine/`. Run these
commands from that folder, after `uv sync`.

| Command | What it does |
| --- | --- |
| `uv run python -m historical_data_backfill_etl.backfill` | Downloads all matches since 2015 (about 1 hour) |
| `uv run python -m historical_data_backfill_etl.validate` | Checks the downloaded match files |
| `uv run python -m weekly_incremental_etl.run` | Adds new results, rebuilds the features and retrains the model |
| `uv run python -m weekly_incremental_etl.run --dry-run` | Lists new matches without changing anything |
| `uv run python -m feature_engineering.build_dataset` | Rebuilds the features only |
| `uv run python -m model.train` | Retrains the model only |
| `uv run python -m model.tune` | Searches for better model settings |
| `uv run python -m model.evaluate` | Tests the model and rewrites `reports/` |
| `uv run python -m model.predict --home Broncos --away Storm --venue "Suncorp Stadium" --date 2026-07-04T09:30:00Z` | Gets the XGBoost forecast alone |

**This repository only includes the 2026 match files.** Run the backfill before
the weekly update, `build_dataset` or `model.train`. Otherwise the model is
rebuilt from one season of data.

## Results and analysis

`Reporting/analysis/analyse_results.py` produces the quantitative results in the
report. Run it from the repository root:

```bash
cd tools/mathematical_engine && uv sync && cd ../..
tools/mathematical_engine/.venv/bin/python Reporting/analysis/analyse_results.py
```

It writes to `Reporting/output/`, `Reporting/figures/` and
`Reporting/Appendix_results.md`.

`Reporting/PREDICTIONS LOG_RESULTS - capstone.md` is the hand-kept results
workbook. It was added to this repository after the testing window, and no
agent code reads it. During the testing window it was kept outside the system,
as NFR-6 required.

**To keep the report's numbers reproducible:**

- A new forecast adds a row to the run log, which the analysis script reads.
- `model.evaluate` replaces the test scores the report uses with those of the
  current model.
- The weekly update and `model.train` replace the trained model.
