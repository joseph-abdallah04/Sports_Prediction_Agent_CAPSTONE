# Agent Architecture

Constrained fact acquisition + LLM judgement + bounded loops. Fact tools use
the **same library entrypoints** as [`tools/mcp_gateway/`](../tools/mcp_gateway/)
(in-process from this package for reliability; MCP remains the host-facing
surface for other clients).

See ADRs in [`adrs/`](adrs/).

## Control flow

```mermaid
flowchart TD
  user[User fixture question]
  orch[Orchestrator]
  scene[set_fixture_scene]
  planQ[LLM query plan]
  research[research_fixture_news]
  gate[Research ok gate]
  math[predict_match from scene]
  judge[Judgement session]
  ver[Checklist plus LLM verifier]
  ledger[Run ledger]

  user --> orch
  orch --> scene
  scene --> planQ
  planQ --> research
  research --> gate
  gate -->|fail once| planQ
  gate -->|pass or done| judge
  scene --> math
  math --> judge
  judge --> ver
  ver -->|feedback same session| judge
  ver -->|pass| out[Final prediction]
  orch --> ledger
```

## Agency

| Layer | Owner |
| --- | --- |
| Tool order | Code |
| Research queries + ≤1 refine | LLM + coverage gate |
| predict args (venue/kickoff/weather) | Code from scene |
| Judgement | LLM session (non-agentic synthesis) |
| Verifier | Checklist + LLM audit; ≤1 recalibrate **without tools** |

## Research ok gate

```text
kept_items_with_body >= 3
AND (official/nrl_news OR availability keywords)
AND NOT all wide-net channels failed empty
```

## Ledger

Every run writes `agent_runs/<run_id>/ledger.json`: request, tool_calls,
agent_steps, research_loop, verifier_loop, final_judgement.
