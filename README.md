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

- **Phase 1 — Data acquisition (ETL backfill):** done. Raw NRL match JSON, 2015-present.
- **Phase 2 — Feature engineering:** done. Leakage-free 49-feature training dataset.
- **Phase 3 — Mathematical core:** done. Optuna-tuned, calibrated XGBoost + SHAP explainer + upcoming-fixture predictor CLI.
- **Phase 4 — Serving:** planned. FastAPI endpoint + weekly retraining ETL.

Start with [`mathematical_engine/README.md`](mathematical_engine/README.md)
for setup and usage, and [`mathematical_engine/Overview.md`](mathematical_engine/Overview.md)
for the system rationale.
