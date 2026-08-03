# NRL Prediction Agent

Constrained-pipeline Orchestrator that calls Capstone fact tools (same
entrypoints as the MCP gateway), authors research queries, judges a winner,
and ledger-audits the run.

Design: [Architecture.md](Architecture.md) · ADRs: [adrs/](adrs/)

## Setup

```bash
cd agent
uv sync
cp .env.example .env   # API keys only — leave empty for local Ollama
```

Provider and model are **not** set here. They live in
[`config.toml`](../config.toml) at the repo root, so the model choice is
committed and reviewable rather than hidden in a git-ignored dotfile
(DD-36). Local Ollama is the default:

```bash
ollama pull gemma4:31b   # must already be pulled
# and make sure `ollama serve` is running
```

LiteLLM is pinned to `<1.80` (wheels without a Rust native build).

## Run a prediction

```bash
uv run python -m agent_app.cli --home Eels --away Panthers

uv run python -m agent_app.cli --home Eels --away Panthers \
  --question "Who wins tonight and why?" -v
```

Each run writes two files:

```
agent_runs/fixtures/2026-R23_Titans-v-Cowboys/20260803T093203Z/
├── ledger.json    complete record — every tool request and response
└── summary.md     the same run, readable
```

Read `summary.md` first; drop to `ledger.json` for the raw evidence. Layout and
ledger structure are documented in [`agent_runs/README.md`](../agent_runs/README.md).

Team names must be official NRL nickNames (`Titans`, `Wests Tigers`, …). The
full list is in the [root README](../README.md#official-nrl-nicknames). Get the
pairing or the home/away order wrong and the run stops in a few seconds with
the round's actual fixtures listed in the error, so you can correct it without
looking anything up.

**Expect a slow run on local Ollama.** A judgement or verifier call against
`gemma4:31b` takes roughly 3 minutes on a 16k-character prompt, so a full run
is typically 6-10 minutes end to end. It is working, not hung — the stage
banners and `LLM responded in …s` lines show progress. A hosted provider
(`LLM_PROVIDER=openai`, etc.) cuts this to well under a minute. Every LLM call
is bounded by `LLM_TIMEOUT_SECONDS` (default 300) with `LLM_MAX_RETRIES`
retries, so a dropped connection fails loudly instead of stalling forever.

## Measure a whole round

One fixture is an anecdote. The harness runs every game in a round and scores
it against the real results afterwards ([ADR 0007](adrs/0007-round-results-harness.md)).

```bash
# before the round — writes agent_runs/rounds/2026-R23/predictions.json
uv run python -m agent_app.harness run --season 2026 --round 23

# after the last game — adds scored.json and summary.md beside it
uv run python -m agent_app.harness score --season 2026 --round 23
```

Because predictions are written before kickoff and scored by a separate
command, results cannot be back-fitted.

Budget the time: 8 fixtures at 6-10 minutes each is roughly an hour on local
Ollama. Run it the evening before the round, not an hour before kickoff.

## Switching models

Edit one line in [`config.toml`](../config.toml):

```toml
[llm]
provider = "bedrock"   # ollama | openai | anthropic | gemini | bedrock
```

Each provider has a `[llm.presets.*]` block holding its model (and region, for
Bedrock), so switching provider brings the right model with it. Put the API key
in `agent/.env`; everything non-secret stays in the committed TOML.

Override for a single run without editing anything:

```bash
uv run python -m agent_app.cli --provider openai --home Titans --away Cowboys
uv run python -m agent_app.cli --provider ollama --model qwen3:8b --home Titans --away Cowboys
```

Check what is actually in effect — useful when four layers can each set a value:

```bash
uv run python -m agent_app.cli --show-config
```

Precedence is defaults < `config.toml` < `agent/.env` < environment variables <
CLI flags. Missing credentials are reported before the run starts rather than
ten minutes into a judgement call.

## Loops

- **Research refine (≤1):** coverage gate fails → sharper queries → one more research call  
- **Verifier recalibrate (≤1):** checklist + LLM audit → same judgement session, **no new tools**

## Judgement guardrails

The judge is deliberately constrained, because unconstrained it inflated
weather, ignored its own research, and invented confidence
([ADR 0006](adrs/0006-grounded-judgement-and-confidence.md)):

- Weather is not a key factor unless SHAP surfaced a weather feature.
- At least one key factor must cite a research article when research found any.
- Confidence stays within 0.10 of the model probability for the picked side,
  caps at 0.85, and caps at 0.60 when picking against the model.

These are checked in code against the ledger, not just asked for in the prompt.

The judge is also told to read availability news for direction — an injury
table's "expected return: round 23" means the player is *back*, not out — after
a run where it reported returning players as missing
([ADR 0008](adrs/0008-verifier-sees-the-evidence.md)).

## Verifier guardrails

The LLM audit gets the research **body excerpts**, not just headlines. Player
names live in article bodies, so a headline-only verifier cannot check whether a
claim is sourced, and when it cannot check it guesses "hallucination" — on one
run it condemned a true injury list and the recalibration loop deleted it
(ADR 0008).

## Design decisions

Each ADR records one decision, the alternatives weighed, and why the others were
rejected. Cross-referenced from [`key_design_decisions.md`](../key_design_decisions.md).

| ADR | Decision |
| --- | --- |
| [0001](adrs/0001-agent-control-loop.md) | Code owns the control loop; the LLM does not choose tools |
| [0002](adrs/0002-llm-provider-config.md) | LiteLLM behind one config surface, local Ollama by default |
| [0003](adrs/0003-agent-authored-research-queries.md) | The agent writes its own research queries |
| [0004](adrs/0004-verifier-recalibrate-in-session.md) | Recalibration re-judges in-session, with no new tool calls |
| [0005](adrs/0005-scene-wires-predict.md) | Scene output wires the math tool's arguments, not the LLM |
| [0006](adrs/0006-grounded-judgement-and-confidence.md) | Judgement is grounded and confidence anchored to the model |
| [0007](adrs/0007-round-results-harness.md) | Measure the agent forward, a whole round at a time |
| [0008](adrs/0008-verifier-sees-the-evidence.md) | The verifier reads article bodies, not just headlines |
