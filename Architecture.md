# System architecture

Three views of the same system: what the components are, how a prediction is
made, and how data moves from nrl.com to a trained model.

Component-level detail lives beside the code:
[`agent/Architecture.md`](agent/Architecture.md) ·
[`tools/mathematical_engine/Overview.md`](tools/mathematical_engine/Overview.md) ·
[`tools/qualitative_research/Architecture.md`](tools/qualitative_research/Architecture.md) ·
[`tools/fixture_scene/Architecture.md`](tools/fixture_scene/Architecture.md) ·
[`tools/mcp_gateway/Architecture.md`](tools/mcp_gateway/Architecture.md)

---

## 1. System view

Three fact tools, one agent. The tools return evidence and never pick a winner;
the agent is the only component allowed to form a judgement.

```mermaid
flowchart TB
    user(["Operator<br/>CLI or harness"])

    subgraph agentbox["agent/ — LLM Orchestrator"]
        orch["Orchestrator<br/><i>owns the control flow</i>"]
        llm["LLM via LiteLLM<br/><i>query plan · judgement · verifier</i>"]
        ledger[("Run ledger<br/>every call, in full")]
        orch <--> llm
        orch --> ledger
    end

    subgraph toolbox["tools/ — fact tools (no judgement)"]
        scene["fixture_scene<br/><i>kickoff, venue, officials, weather</i>"]
        research["qualitative_research<br/><i>injuries, Late Mail, form</i>"]
        maths["mathematical_engine<br/><i>calibrated P(home win) + SHAP</i>"]
    end

    mcp["mcp_gateway<br/><i>same tools over MCP</i>"]
    external(["External MCP host<br/>e.g. Claude Desktop"])

    nrl[("nrl.com")]
    news[("Google News RSS<br/>DuckDuckGo<br/>nrl.com news")]
    meteo[("Open-Meteo")]
    store[("data lake +<br/>feature store +<br/>trained model")]

    user --> orch
    orch -->|1 . always first| scene
    orch -->|2 . in parallel| research
    orch -->|2 . in parallel| maths

    scene --> nrl
    scene --> meteo
    research --> news
    maths --> store

    scene -.-> mcp
    research -.-> mcp
    maths -.-> mcp
    mcp -.-> external

    classDef tool fill:#eef6ff,stroke:#4a7fb5
    classDef data fill:#f6f6f6,stroke:#999
    class scene,research,maths tool
    class nrl,news,meteo,store,ledger data
```

The scene tool runs first and unconditionally, because its output supplies the
arguments for the other two: the venue, kickoff and weather label handed to
`predict_match` come from the scene rather than from the LLM
([ADR 0005](agent/adrs/0005-scene-wires-predict.md)). That is what stops the
model being asked to predict a match at a venue the LLM invented.

---

## 2. Agent control loop

The code decides which tool runs and when. The LLM contributes judgement at
three fixed points and never chooses a tool
([ADR 0001](agent/adrs/0001-agent-control-loop.md)).

```mermaid
flowchart TD
    start(["run_prediction()"]) --> scene["1 . set_fixture_scene<br/><i>code</i>"]
    scene --> plan["2 . Query plan<br/><b>LLM</b> writes search queries"]
    plan --> merge["Merge with default templates<br/><i>code — DD-29</i>"]

    merge --> par{{"3 . Run in parallel"}}
    par --> research["research_fixture_news<br/><i>code</i>"]
    par --> maths["predict_match<br/><i>code, args from scene</i>"]

    research --> gate{"Research gate<br/><i>code</i><br/>≥3 items with body?<br/>official or availability source?<br/>not every channel failed?"}
    maths --> judge

    gate -->|fail, once only| refine["Refine queries<br/><b>LLM</b>"]
    refine --> research
    gate -->|pass| judge["4 . Judgement<br/><b>LLM</b> synthesises scene + research + maths"]

    judge --> checklist{"5a . Coded checklist<br/><i>confidence bounds, weather rule,<br/>research grounding</i>"}
    checklist --> audit{"5b . LLM audit<br/><b>LLM</b> reads the ledger<br/><i>with article bodies</i>"}

    audit -->|fail, once only| recal["Recalibrate<br/><b>LLM</b>, same session,<br/><i>no new tools</i>"]
    recal --> done
    audit -->|pass| done["6 . Write ledger + summary"]

    done --> out(["Prediction"])

    classDef llm fill:#fff3e0,stroke:#e08a3c
    classDef code fill:#eef6ff,stroke:#4a7fb5
    class plan,refine,judge,recal,audit llm
    class scene,research,maths,merge,checklist code
```

Both loops are capped at one iteration. Two things are worth noticing:

- **The gate is code, not the LLM.** Whether research is good enough is decided
  by counting items and checking sources, so it cannot be talked around.
- **The checklist runs before the LLM audit.** Anything decidable from the
  ledger — confidence within 0.10 of the model probability, no weather claim
  without a weather SHAP driver, at least one research-sourced factor — is
  checked in code, because the verifier LLM is exactly as fallible as the judge
  ([ADR 0006](agent/adrs/0006-grounded-judgement-and-confidence.md),
  [ADR 0008](agent/adrs/0008-verifier-sees-the-evidence.md)).

---

## 3. Data flow: nrl.com to a trained model

```mermaid
flowchart LR
    subgraph acquire["Acquisition"]
        nrl[("nrl.com<br/>match centre")]
        backfill["historical_data_backfill_etl<br/><i>one-off, 2015→</i>"]
        weekly["weekly_incremental_etl<br/><i>every round</i>"]
        lake[("data_lake/<br/>2,382 raw match JSON")]
        nrl --> backfill --> lake
        nrl --> weekly --> lake
    end

    subgraph features["Feature engineering"]
        flat["Stage 1 · flatten.py<br/><i>nested JSON → table</i>"]
        flatp[("matches_flat.parquet<br/>2,366 × 103")]
        s2["Stage 2<br/>ratings · context ·<br/>standings · rolling form"]
        train[("training_dataset.parquet<br/>2,366 × 69 — 61 features")]
        lake --> flat --> flatp --> s2 --> train
    end

    subgraph model["Model"]
        tune["tune.py<br/><i>Optuna, occasional</i>"]
        fit["train.py<br/><i>XGBoost + sigmoid calibration</i>"]
        artifacts[("models/<br/>model.ubj · calibrator ·<br/>best_params · feature columns")]
        eval["evaluate.py<br/><i>2025-26 holdout</i>"]
        ab["feature_ab.py<br/><i>A/B before shipping features</i>"]
        train --> tune --> fit --> artifacts
        train --> eval
        train --> ab
    end

    subgraph serve["Inference"]
        fixture(["Upcoming fixture<br/>teams · venue · kickoff · weather"])
        infer["inference.py<br/><i>synthetic row, same Stage 2 code</i>"]
        predict["serving.predict_fixture()"]
        shap["explain.py<br/><i>SHAP drivers</i>"]
        fixture --> infer --> predict --> shap
        artifacts --> predict
        train --> infer
    end

    classDef store fill:#f6f6f6,stroke:#999
    class lake,flatp,train,artifacts store
```

Two properties this shape is designed to guarantee:

- **No leakage.** Every feature attached to a match is computed only from
  matches that kicked off earlier. Ratings, ladder position and rolling form are
  all built by walking the table in chronological order, and the holdout seasons
  (2025–2026) are never touched during tuning or training.
- **No train/serve skew.** The inference path appends a synthetic row for the
  upcoming fixture and runs *the same Stage 2 functions* over it. A parity test
  checks that features built this way for a historical match equal the ones the
  model trained on.

---

## 4. Where results land

```
agent_runs/
├── fixtures/2026-R23_Titans-v-Cowboys/20260803T093203Z/
│   ├── ledger.json      complete record — every tool request and response
│   └── summary.md       the same run, readable
└── rounds/2026-R23/
    ├── predictions.json written BEFORE kickoff
    ├── scored.json      written AFTER the games, by a separate command
    └── summary.md       the scorecard
```

See [`agent_runs/README.md`](agent_runs/README.md) for how to read a ledger.
