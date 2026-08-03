# Fixture Scene Tool

Compulsory first tool in the agent pipeline: resolve an upcoming NRL fixture
from nrl.com and attach a free kickoff-time weather forecast. Returns
**structured facts only** (no LLM) for the Orchestrator.

Full design: [Architecture.md](Architecture.md).

Agent access: MCP tool `set_fixture_scene` via [`mcp_gateway/`](../mcp_gateway/README.md).

## Setup

```bash
cd fixture_scene
uv sync
```

## Set the scene (CLI)

```bash
uv run python -m scene.cli --home Eels --away Panthers

# Optional round / season / force refresh
uv run python -m scene.cli --home Eels --away Panthers --round 21 --force-refresh

# Append tool call to a ledger file (for Verifier later)
uv run python -m scene.cli --home Eels --away Panthers \
  --write-ledger ../../agent_runs/demo/ledger.json
```

## What it returns

- Fixture: season, round, kickoff, venue, officials, team lists (soft-null if unavailable)
- Weather: Open-Meteo hourly at kickoff + `math_weather_label` (`Fine` / `Rain` / `unknown`) for the math engine
- Sources: draw URL, match centre URL, weather URL

Same fixture same calendar day (AU/Sydney) is served from `cache/` unless `--force-refresh`.
