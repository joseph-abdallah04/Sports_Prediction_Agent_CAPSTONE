# Qualitative Research Tool

Zero-cost multi-channel research for upcoming NRL fixtures. Returns
**structured facts only** (no LLM, no winner prediction) for the agent
Orchestrator.

Full design: [Architecture.md](Architecture.md).

Agent access: MCP tool `research_fixture_news` via [`mcp_gateway/`](../mcp_gateway/README.md).
Optional `queries: list[str]` overrides default search templates (agent path;
CLI omits and keeps built-in templates; capped at 6).

## Setup

```bash
cd qualitative_research
uv sync
```

## Research a fixture (CLI)

```bash
uv run python -m research.cli \
  --home Eels --away Panthers \
  --kickoff 2026-07-25T19:30:00+10:00 \
  --round 21

# Force fresh fetch (ignore day cache)
uv run python -m research.cli --home Eels --away Panthers \
  --kickoff 2026-07-25T19:30:00+10:00 --round 21 --force-refresh

# After a fresh run, inspect what the filter dropped (local audit only —
# not in the API/CLI JSON response or day cache):
#   debug/dropped/<cache_key>.json

# Append tool call to a ledger file (for Verifier later)
uv run python -m research.cli --home Eels --away Panthers \
  --kickoff 2026-07-25T19:30:00+10:00 --round 21 \
  --write-ledger ../../agent_runs/demo/ledger.json
```

## Channels

1. **nrl.com** — official news (Team Lists, Injuries, Match Preview, club pages)
2. **DuckDuckGo news** — wide discovery (injuries / Late Mail / form — not weather/ref)
3. **Google News RSS** — backup discovery (same query templates)
4. **Reddit r/nrl** — low-trust community signal

Kickoff, venue, officials, and weather come from
[`fixture_scene`](../fixture_scene/README.md) — research queries intentionally
omit those.

Same fixture same calendar day is served from `cache/` unless `--force-refresh`.
