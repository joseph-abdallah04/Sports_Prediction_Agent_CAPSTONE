# ADR 0005: Scene wires predict_match args

## Status

Accepted

## Context

`predict_match` needs venue, kickoff, and optional weather. The LLM should not
invent these; scene already resolves them.

## Decision

Orchestrator code sets:

- `venue` / `kickoff` from scene fixture  
- `weather` from `scene.weather.math_weather_label`  

No LLM override of weather or feature vectors on the main run.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| LLM chooses weather / venue | Hallucination risk; breaks train/serve parity |
| Counterfactual weather as main path | Confuses primary prediction (optional later) |

## Consequences

Math tool signature unchanged; agent path is deterministic from scene.
