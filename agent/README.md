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
ollama pull gemma4:31b-mlx   # must already be pulled
# and make sure `ollama serve` is running
```

LiteLLM is pinned to `<1.80` (wheels without a Rust native build).

## Run a prediction

```bash
uv run python -m agent_app.cli --home Eels --away Panthers

uv run python -m agent_app.cli --home Eels --away Panthers \
  --question "Who wins tonight and why?" -v
```

Each run writes four files, and appends a row to one more:

```
agent_runs/
├── fixtures/2026-R23_Titans-v-Cowboys/20260803T093203Z/
│   ├── ledger.json    complete record — every tool request and response
│   ├── record.json    the run's numbers, flattened for a write-up
│   ├── summary.md     the same run, readable
│   └── thinking.md    model scratchpad (real thinking, when available)
└── predictions_log.csv   one appended row per prediction, ever
```

Read `summary.md` first, take numbers from `predictions_log.csv`, open
`thinking.md` for the model's scratchpad, and drop to `ledger.json` for the
raw evidence. Layout and ledger structure are documented in
[`agent_runs/README.md`](../agent_runs/README.md); the full operating guide is
[`HOWTOUSE.md`](../HOWTOUSE.md).

Team names must be official NRL nickNames (`Titans`, `Wests Tigers`, …). The
full list is in the [root README](../README.md#official-nrl-nicknames). Get the
pairing or the home/away order wrong and the run stops in a few seconds with
the round's actual fixtures listed in the error, so you can correct it without
looking anything up.

**Expect a slow run on local Ollama.** A judgement or verifier call against
`gemma4:31b-mlx` takes roughly 3–5 minutes on a 16k-character prompt with
thinking enabled, so a full run
is typically 10–20 minutes end to end. It is working, not hung — the stage
banners and `LLM responded in …s` lines show progress. A hosted provider
(`LLM_PROVIDER=openai`, etc.) cuts this to well under a minute. Every LLM call
is bounded by `LLM_TIMEOUT_SECONDS` (default 600 in `config.toml`) with
`LLM_MAX_RETRIES` retries, so a dropped connection fails loudly instead of
stalling forever.

## Measure a whole round

One fixture is an anecdote. The harness runs every game in a round and scores
it against the real results afterwards ([ADR 0007](adrs/0007-round-results-harness.md)).

```bash
# what is still ahead of kickoff, and when (2 seconds, no LLM)
uv run python -m agent_app.harness run --season 2026 --round 23 --dry-run

# predict what is left — writes agent_runs/rounds/2026-R23/predictions.json
uv run python -m agent_app.harness run --season 2026 --round 23

# after the last game — adds scored.json and summary.md beside it
uv run python -m agent_app.harness score --season 2026 --round 23
```

### Running a round that spans four days

An NRL round starts Thursday and ends Sunday, so predicting all eight games at
once judges the Sunday fixtures on Wednesday's team lists. `run` is therefore
incremental: it appends to `predictions.json`, skips fixtures already predicted,
and **refuses to predict a fixture whose kickoff has passed**. So you can work
match day by match day and still keep an honest pre-kickoff record of every
game:

```bash
# Wednesday night, for Thursday's game
uv run python -m agent_app.harness run --season 2026 --round 23 --only Titans

# Friday afternoon, for the Friday and Saturday games
uv run python -m agent_app.harness run --season 2026 --round 23

# Sunday morning, for the last two
uv run python -m agent_app.harness run --season 2026 --round 23
```

Because predictions are written before kickoff and scored by a separate
command, and a played fixture is refused rather than predicted, results cannot
be back-fitted.

Budget the time: 6-10 minutes per fixture on local Ollama, so roughly an hour
for all eight, or about half that for a three-game Saturday. Start well before
the first kickoff of the day you are predicting — the run has to finish before
the game starts to count.

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

The judge is deliberately constrained, because unconstrained it inflated weather
and ignored its own research
([ADR 0006](adrs/0006-grounded-judgement-and-confidence.md)):

- Weather is not a key factor unless SHAP surfaced a weather feature
  (prompt + LLM audit `weather_not_headline` — not a coded keyword check).
- At least one key factor must cite a research article when research found any
  (prompt + coded checklist).

The research-use rule is checked in code against the ledger. Weather is left to
the audit: a keyword scan once treated "hamstring strain" as weather and burned
a recalibration on a false positive.

The judge is also told to read availability news for direction — an injury
table's "expected return: round 23" means the player is *back*, not out — after
a run where it reported returning players as missing
([ADR 0008](adrs/0008-verifier-sees-the-evidence.md)).

### Confidence is the agent's own number

Confidence used to be pinned within 0.10 of the model probability. It is not any
more: pinning them made the agent's Brier score a restatement of the model's, so
the comparative evaluation could not have found a difference even if one existed
([ADR 0009](adrs/0009-confidence-is-the-agents-own-number.md)).

Overconfidence is handled in the prompt instead — the number is framed as a
frequency claim, given explicit bands, and preceded by naming the strongest
reason the pick could lose. Only two bounds are enforced in code, neither derived
from the model: a floor of 0.50, below which the judge would have contradicted
its own `winner`, and a ceiling of 0.95.

Expect the agent's calibration to be the weaker half of the result. That is the
honest measurement, and `math_home_win_prob` sits beside `confidence` in every
record so the gap between them is observable rather than clamped away.

## Before a round, run the smoke test

```bash
uv run python scripts/smoke_orchestrator.py
```

Runs the whole control loop offline in about two seconds, with the fact tools
and the LLM stubbed, and asserts that every stage executed and wrote what it
should — including the recalibration loop, which a healthy real run never
exercises. It exists because a mistyped function name once crashed a live run at
stage five, eleven minutes in. Two seconds beforehand is cheaper than an hour of
a round spent finding out.

## Verifier guardrails

The LLM audit gets the research **body excerpts**, not just headlines. Player
names live in article bodies, so a headline-only verifier cannot check whether a
claim is sourced, and when it cannot check it guesses "hallucination" — on one
run it condemned a true injury list and the recalibration loop deleted it
(ADR 0008).

It also has to show its work. The audit returns one entry per check with the
evidence it matched, kept in the ledger pass or fail, because a bare
`pass: true` is indistinguishable from a verifier that never looked (DD-38).

Two flags, not one: `verifier_ran` says the checks happened,
`recalibration_triggered` says they sent the judgement back. A clean run is
`true` then `false`.

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
| [0006](adrs/0006-grounded-judgement-and-confidence.md) | Judgement is grounded (confidence rule superseded by 0009) |
| [0007](adrs/0007-round-results-harness.md) | Measure the agent forward, a whole round at a time |
| [0008](adrs/0008-verifier-sees-the-evidence.md) | The verifier reads article bodies, not just headlines |
| [0009](adrs/0009-confidence-is-the-agents-own-number.md) | Confidence is the agent's own number, not the model's |
| [0010](adrs/0010-record-file-and-running-log.md) | A short record per run, and one append-only log |
