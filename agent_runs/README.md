# Agent run output

Everything the agent produces lands here. The directory is git-ignored — these
are results, not source — but this file is committed so the layout is
documented alongside the code that writes it.

```
agent_runs/
├── README.md                              this file
├── fixtures/
│   └── 2026-R23_Titans-v-Cowboys/         one folder per fixture
│       ├── 20260803T093203Z/              one folder per run of that fixture
│       │   ├── ledger.json                complete, unabridged record
│       │   └── summary.md                 the same run, readable
│       └── 20260803T101500Z/              a later run of the same game
├── rounds/
│   └── 2026-R23/
│       ├── predictions.json               written BEFORE kickoff
│       ├── scored.json                    written AFTER the games
│       └── summary.md                     the scorecard, readable
└── archive/                               runs from before this layout existed
```

`summary.md` is rewritten at every stage of a run, so opening it mid-run shows
how far the agent has got rather than a stale or empty file.

## Which file do I want?

| Question | File |
| --- | --- |
| What did it predict, and why? | `fixtures/<fixture>/<run>/summary.md` |
| Exactly what did each tool return? | `fixtures/<fixture>/<run>/ledger.json` |
| Did the agent beat the model this round? | `rounds/<round>/summary.md` |
| What was predicted before kickoff? | `rounds/<round>/predictions.json` |

Start with `summary.md`. Drop to `ledger.json` when you need the raw evidence —
every bug worth finding in this project was found by reading a ledger, not by
reading the answer.

## Reading a ledger

`ledger.json` is written most-summarised-first:

| Key | What it holds |
| --- | --- |
| `at_a_glance` | Derived one-screen summary: fixture, pick, confidence, model probability, whether either loop fired |
| `request` | What the run was asked for, including the provider and model used |
| `error` | Non-null only if the run failed |
| `final_judgement` | The prediction the agent settled on |
| `research_loop` | Gate diagnostics, queries before and after any refine |
| `verifier_loop` | Coded checklist, LLM audit, and the judgement before/after any recalibration |
| `agent_steps` | Each LLM step in order |
| `tool_calls` | Every tool request and full response, with timings |

`at_a_glance` is *derived* — it summarises fields that appear in full further
down. Nothing is ever removed from a ledger, so any figure in a summary can be
traced back to the tool response that produced it.

Multiple runs of the same fixture sit side by side under one folder,
timestamped, which is how you compare a prediction made on Monday against one
made after Thursday's team lists.

## Why predictions and scores are separate files

`predictions.json` is written before the round is played; `scored.json` is
written by a separate command afterwards and reads that file back. The
separation is the point, not a convenience: it makes back-fitting structurally
impossible ([ADR 0007](../agent/adrs/0007-round-results-harness.md)).
