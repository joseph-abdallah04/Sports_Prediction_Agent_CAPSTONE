# Qualitative Research Tool

Zero-cost multi-channel research for upcoming NRL fixtures. Returns
**structured facts only** (no LLM, no winner prediction) for the agent
Orchestrator.

Full design: [Architecture.md](Architecture.md).

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
  --write-ledger ../agent_runs/demo/ledger.json
```

## HTTP API

```bash
uv run uvicorn api.main:app --host 127.0.0.1 --port 8001
```

```bash
curl -s http://127.0.0.1:8001/health

curl -s -X POST http://127.0.0.1:8001/research \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Eels",
    "away_team": "Panthers",
    "kickoff": "2026-07-25T19:30:00+10:00",
    "round_number": 21
  }'
```

Docs: http://127.0.0.1:8001/docs

## Channels

1. **nrl.com** — official news (Team Lists, Injuries, Match Preview, club pages)
2. **DuckDuckGo news** — wide discovery
3. **Google News RSS** — backup discovery
4. **Reddit r/nrl** — low-trust community signal

Same fixture same calendar day is served from `cache/` unless `--force-refresh`.
