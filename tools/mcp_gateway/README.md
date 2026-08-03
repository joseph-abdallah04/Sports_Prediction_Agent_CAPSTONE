# MCP Gateway

Single [Model Context Protocol](https://modelcontextprotocol.io) server that
exposes Capstone **fact tools** to an agent client.

Design: [Architecture.md](Architecture.md).

## Tools

| MCP tool | Package | Role |
| --- | --- | --- |
| `set_fixture_scene` | `fixture_scene` | Kickoff, venue, officials, team lists, weather label |
| `research_fixture_news` | `qualitative_research` | Injuries / Late Mail / form (optional `queries`) |
| `predict_match` | `mathematical_engine` | Calibrated P(home win) + SHAP |
| `tools_health` | gateway | Readiness / model artifact status |

## Setup

```bash
cd tools/mcp_gateway
uv sync
```

Editable path deps pull in the three tool packages (CLI packages stay
installable on their own).

## Run the server (stdio)

```bash
uv run python -m gateway
# or: uv run nrl-mcp
```

Configure your MCP host (Cursor / future Capstone agent) to launch that
command with cwd `tools/mcp_gateway/`.

## Operator testing without MCP

Each tool still has a CLI — preferred for human debugging:

```bash
cd ../fixture_scene && uv run python -m scene.cli --home Eels --away Panthers
cd ../qualitative_research && uv run python -m research.cli ...
cd ../mathematical_engine && uv run python -m model.predict ...
```

## Smoke (library path)

```bash
uv run python scripts/smoke_tools.py
```
