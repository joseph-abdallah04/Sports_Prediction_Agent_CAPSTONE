# NRL Prediction Agent

Constrained-pipeline Orchestrator that calls Capstone fact tools (same
entrypoints as the MCP gateway), authors research queries, judges a winner,
and ledger-audits the run.

Design: [Architecture.md](Architecture.md) · ADRs: [adrs/](adrs/)

## Setup

```bash
cd agent
uv sync
cp .env.example .env   # set LLM_PROVIDER / LLM_MODEL
```

Local Ollama (default):

```bash
# Default local model (must already be pulled in Ollama)
ollama pull gemma4:31b
# ensure ollama serve is running
```

LiteLLM is pinned to `<1.80` (wheels without a Rust native build).

## Run a prediction

```bash
uv run python -m agent_app.cli --home Eels --away Panthers

uv run python -m agent_app.cli --home Eels --away Panthers \
  --question "Who wins tonight and why?" -v
```

Writes `agent_runs/<run_id>/ledger.json` (full tool I/O, loops, judgements).

## LLM providers

| Env | Example |
| --- | --- |
| `LLM_PROVIDER=ollama` | `LLM_MODEL=gemma4:31b` |
| `LLM_PROVIDER=openai` | `LLM_MODEL=gpt-4o-mini` + `OPENAI_API_KEY` |
| `LLM_PROVIDER=anthropic` | `LLM_MODEL=claude-sonnet-4-20250514` + `ANTHROPIC_API_KEY` |
| `LLM_PROVIDER=gemini` | `LLM_MODEL=gemini-2.0-flash` + `GEMINI_API_KEY` |
| `LLM_PROVIDER=bedrock` | `LLM_MODEL=anthropic.claude-...` + AWS creds / region |

## Loops

- **Research refine (≤1):** coverage gate fails → sharper queries → one more research call  
- **Verifier recalibrate (≤1):** checklist + LLM audit → same judgement session, **no new tools**
