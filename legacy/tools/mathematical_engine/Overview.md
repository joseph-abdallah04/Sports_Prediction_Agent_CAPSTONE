# Capstone Project: Deterministic Mathematical Engine Architecture

## 1. Executive Summary & Rationale

Current Large Language Models (LLMs) struggle natively with time-series numerical data and mathematical computation, often leading to logic hallucinations. In the high-variance domain of professional sports forecasting (NRL), relying on an LLM to "calculate" form or momentum is architecturally flawed.

To mitigate this, our multi-agent system strictly separates cognitive concerns. The LLM Orchestrator handles semantic reasoning (e.g., news, injury reports) but explicitly delegates all statistical analysis to a Deterministic Mathematical Engine. This engine utilizes traditional machine learning algorithms to crunch highly granular match telemetry and returns not just a probability, but mathematically grounded reasoning (via SHAP) to the Orchestrator. A final Judge agent then verifies the Orchestrator's combined reasoning.

## 2. Core Stack

- **Language:** Python (Aligned with standard data engineering practices)
- **Data Processing:** Pandas
- **Storage:** Parquet (Local Data Lake)
- **Machine Learning Model:** XGBoost Classifier
- **Interpretability Framework:** SHAP (SHapley Additive exPlanations)
- **API / agent integration:** MCP gateway (`../mcp_gateway/`) — not per-tool FastAPI

## 3. Phase 1: Data Acquisition (The ETL Pipeline)

To train an accurate XGBoost model without missing values (nulls) in advanced metrics (like Post-Contact Metres), the system relies on data from the modern "Telemetry Era" (2015–Present).

The ETL architecture is split into two distinct operational flows:

### 3.1 Job A: The Historical Backfill (One-Off Execution)

A singular, bulk-processing pipeline used to establish the foundational Data Lake.

- **Dynamic Draw Scraper:** A Python script iterates through the years 2015 to 2026, parsing the nrl.com/draw URLs to extract the specific match-centre link for all historical games.
- **Mass Payload Extraction:** The scraper hits the ~2,200 extracted URLs, targets the embedded vue-match-centre JSON state-hydration layer, and dumps the raw structured JSON into a data_lake/raw_historical/ directory.

### 3.2 Job B: The Incremental Pipeline (Weekly Ongoing Execution)

A lightweight, scheduled pipeline designed to maintain model accuracy during an active season.

- **Static URL Feed:** Each week, a list of the 8 upcoming/completed match URLs is fed into the script.
- **Transform & Append:** The script extracts the JSON payload for the new round, applies the transformation logic, and appends the new rows to the existing Parquet Data Lake.
- **Automated Retraining:** Following the append, a trigger automatically retrains the XGBoost model on the newly updated Parquet files so it is perfectly calibrated for the upcoming weekend.

## 4. Phase 2: Feature Engineering & Transformation

The raw nested JSON must be flattened into a structured 1D row per match. The transformation logic categorizes features into five distinct pillars.

### A. Power Ratings (Long-Term Baseline)

- **Rolling Elo Differential:** The difference in Elo rating between the Home and Away team.
- **Crucial Logic:** We apply Off-Season Mean Reversion. Ratings are not reset to zero at the start of a new season; they are regressed ~30% toward the league average to reflect roster changes while maintaining foundational team quality. This rolling calculation begins from the first match of 2015.
- **Pythagorean Winning Percentage:** Expected win rate based on the ratio of points scored vs. conceded over a rolling 10-game window.
- **Bradley-Terry Model Rating:** Pairwise comparison probability isolating pure team strength.

### B. Environmental Context

- **Quantified Home-Ground Advantage:** Venues are weighted based on historical win correlations, not just a binary 1/0.
- **Rest Days:** Turnaround time since the team's last match (e.g., 5 days vs. 8 days).
- **Interstate Travel Flag:** Binary flag capturing travel fatigue.
- **Weather Modifiers:** Dynamic weighting for "Rain" vs. "Fine" correlating with a team's historical wet-weather completion rates.

### C. Granular Telemetry (Short-Term Form)

Calculated as rolling averages over the last 3 and 5 games using the stats.groups array:

- **The Grind:** Post-Contact Metres, Kick Metres, Play-The-Ball Speed.
- **Efficiency:** Net Possession %, Completion Rate Differential.
- **Defence & Discipline:** Effective Tackle %, Missed Tackles, Total Errors, Penalties Conceded.

### D. Momentum & Fatigue (Timeline Parsing)

Calculated using the timeline array's gameSeconds:

- **Late-Game Fatigue Rating:** Net score differential in the final 20 minutes (gameSeconds 3600 to 4800).
- **Penalty Clusters:** Frequency/time between conceded penalties (measuring loss of discipline).
- **First-to-Score Win %:** Correlating early momentum to final outcomes.

### E. Roster Resilience (Player Workload)

- **Workload Distribution:** Measuring the percentage of a team's total run metres/tackles handled by their top 3 players. A more distributed workload indicates mathematical resilience against in-game injuries.

## 5. Phase 3: Storage

The flattened Pandas DataFrames are saved locally as Parquet files. Parquet is chosen over CSV because it is heavily compressed, strictly maintains data types (crucial for XGBoost compatibility), and allows for highly efficient read/append operations during the weekly Incremental Pipeline.

## 6. Phase 4: The Mathematical Core (XGBoost & SHAP)

### Algorithm Selection

XGBoost is utilized as the core predictive model. In the sports analytics industry, gradient boosting is the gold standard for tabular data. It outperforms deep learning on smaller datasets (~2,200 games) and handles complex, non-linear interactions between variables (e.g., a team with high possession but terrible completion rates).

### Interpretability for the LLM Orchestrator

The fatal flaw of standard multi-agent systems is passing a "black box" number to an LLM. To solve this, the XGBoost model is wrapped in a SHAP explainer. SHAP calculates exactly how much each transformed feature shifted the prediction away from the baseline.

### Tool integration (The Hand-off)

The XGBoost model and SHAP explainer are exposed via the shared
`predict_fixture()` function (CLI `model.predict` and MCP tool
`predict_match`). When the LLM Orchestrator requires a mathematical baseline,
it calls that tool and receives a heavily contextualized JSON payload:

```json
{
  "prediction": "Home Win",
  "probability": 0.74,
  "shap_explanations": {
    "positive_drivers": [
      "home_rolling_elo_differential (+110 points)",
      "home_rolling_completion_rate (+6.5% vs opponent)",
      "away_rest_days (Only 5 days rest)"
    ],
    "negative_drivers": [
      "home_fatigue_rating_last_20_mins (-8 points vs opponent)",
      "home_missed_tackles_avg (Higher than league average)"
    ]
  }
}
```

**Outcome:** The Orchestrator does no mathematical calculation. It reads this deterministic output, translates it into natural language, cross-references it against its own semantic analysis (e.g., verifying if the "missed tackles" driver is exacerbated by breaking injury news), and forwards a synthesized, hallucination-free argument to the Judge agent for final verification.