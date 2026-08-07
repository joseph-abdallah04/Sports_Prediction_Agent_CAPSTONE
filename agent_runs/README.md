# Agent run output

Everything the agent produces lands here. The directory is git-ignored — these
are results, not source — but this file is committed so the layout is
documented alongside the code that writes it.

```
agent_runs/
├── README.md                              this file
├── predictions_log.csv                    every prediction ever, one row each
├── fixtures/
│   └── 2026-R23_Titans-v-Cowboys/         one folder per fixture
│       ├── 20260803T093203Z/              one folder per run of that fixture
│       │   ├── ledger.json                complete, unabridged record
│       │   ├── record.json                the run's numbers, flattened
│       │   ├── summary.md                 the same run, readable
│       │   └── thinking.md                model scratchpad (real thinking)
│       └── 20260803T101500Z/              a later run of the same game
├── rounds/
│   └── 2026-R23/
│       ├── predictions.json               written BEFORE kickoff
│       ├── scored.json                    written AFTER the games
│       └── summary.md                     the scorecard, readable
└── archive/                               runs from before this layout existed
```

`summary.md` is rewritten at every stage of a run, so opening it mid-run shows
how far the agent has got rather than a stale or empty file. `record.json` and
the log row are written once, at the end, on every exit path — a failed run
still leaves a row saying it failed, because a prediction missing from the log
is indistinguishable from a round nobody ran.

## Which file do I want?

| Question | File |
| --- | --- |
| **The numbers, for calculating metrics by hand** | **`predictions_log.csv`** |
| The same numbers for a single run | `fixtures/<fixture>/<run>/record.json` |
| What did it predict, and why? | `fixtures/<fixture>/<run>/summary.md` |
| What was the model thinking? | `fixtures/<fixture>/<run>/thinking.md` |
| Exactly what did each tool return? | `fixtures/<fixture>/<run>/ledger.json` |
| Did the agent beat the model this round? | `rounds/<round>/summary.md` |
| What was predicted before kickoff? | `rounds/<round>/predictions.json` |

Start with `summary.md`. Drop to `ledger.json` when you need the raw evidence —
every bug worth finding in this project was found by reading a ledger, not by
reading the answer.

## The running log

`predictions_log.csv` is **append-only**. It accumulates one row per prediction
across the entire testing window and is the single table the evaluation is
calculated from ([ADR 0010](../agent/adrs/0010-record-file-and-running-log.md)).

Its last seven columns — `actual_winner`, `actual_home_score`,
`actual_away_score`, `vanilla_llm_winner`, `vanilla_llm_confidence`,
`statsinsider_home_prob`, `notes` — are never written by the agent. They are
there to be filled in by hand after each round. Because existing lines are never
rewritten, those edits survive every later run.

Two columns worth understanding: `confidence` is the agent's confidence in its
own pick and is **not** derived from the maths model, while
`math_home_win_prob` is what the tool said on its own. Scoring them separately
is the point — anchoring them would make the agent's Brier score a restatement
of the model's (DD-41,
[ADR 0009](../agent/adrs/0009-confidence-is-the-agents-own-number.md)).

If a spreadsheet holds the file open when a run finishes, the append can fail.
The run is unaffected and `record.json` still holds the numbers, so the row can
be recovered from the run folder.

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

### Did the loops run?

Each loop records two separate things, because "the check happened" and "the
check changed something" are different questions:

| Field | Meaning |
| --- | --- |
| `verifier_loop.verifier_ran` | Whether the checklist and LLM audit executed at all |
| `verifier_loop.recalibration_triggered` | Whether they sent the judgement back to be redone |
| `research_loop.triggered` | Whether the research gate failed and queries were rewritten |

A healthy run is `verifier_ran: true` with `recalibration_triggered: false`:
the verifier looked and found nothing to fix. That is the common case, not a
sign the verifier was skipped.

`verifier_loop.llm_audit.checks` lists every check the audit performed with the
evidence it matched, so a pass is reviewable rather than a bare assertion
(DD-38). `summary.md` renders it as a table.

Multiple runs of the same fixture sit side by side under one folder,
timestamped, which is how you compare a prediction made on Monday against one
made after Thursday's team lists.

## Why predictions and scores are separate files

`predictions.json` is written before the round is played; `scored.json` is
written by a separate command afterwards and reads that file back. The
separation is the point, not a convenience: it makes back-fitting structurally
impossible ([ADR 0007](../agent/adrs/0007-round-results-harness.md)).
