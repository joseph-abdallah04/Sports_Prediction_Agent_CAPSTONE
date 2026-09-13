# Fact tools

Deterministic Capstone tools the agent calls via MCP (and humans via CLI).

| Package | Role |
| --- | --- |
| [`mathematical_engine/`](mathematical_engine/README.md) | ETL, features, XGBoost + SHAP (`predict_match`) |
| [`fixture_scene/`](fixture_scene/README.md) | Kickoff / venue / officials / weather (`set_fixture_scene`) |
| [`qualitative_research/`](qualitative_research/README.md) | Injuries / Late Mail / form news (`research_fixture_news`) |
| [`mcp_gateway/`](mcp_gateway/README.md) | One MCP server exposing the three tools |

Agent package (LLM Orchestrator): [`../agent/`](../agent/README.md).
