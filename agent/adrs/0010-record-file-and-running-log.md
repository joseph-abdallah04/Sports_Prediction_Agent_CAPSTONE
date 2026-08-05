# ADR 0010: A record file per run and one running log

## Status

Accepted. Indexed as DD-42 in `key_design_decisions.md`.

## Context

The ledger holds everything a run did: every tool request and response, every
article body, every verifier check. That completeness is the point of it, and it
is exactly what makes it the wrong file to read a confidence score out of on a
Sunday evening. A single run's ledger is several hundred lines, and the numbers
needed to write up a round are scattered through it — the prediction in
`final_judgement`, the model probability inside a `tool_calls` response, the
research titles inside another, the verifier verdict in `verifier_loop`.

`summary.md` renders a readable narrative, but prose is not something you can
total up across five rounds.

The evaluation is manual: after each round the results, the two control systems'
predictions, accuracy, reliability and Brier are worked out by hand. That
workflow needs a table, and it needs the machine never to touch the cells that
were typed in by hand.

## Decision

Every run writes two things in addition to the ledger and summary.

**`record.json`, beside the ledger.** A flat, small projection of the run:
identity and timing (including `hours_before_kickoff`, so how fresh a prediction
was is a recorded fact rather than an inference from timestamps), the fixture,
the prediction with confidence and its conversion to P(home win), the model's
probability and SHAP drivers kept *separately* from the prediction, the research
actually used with citable domain and publication date, the verifier's checks
and verdicts, and the judge's reasoning. Derived purely from the ledger, with no
LLM and no network, so any past run's record can be rebuilt.

**`agent_runs/predictions_log.csv`, one row per prediction ever made.** Written
in append mode only. The header ends in seven columns the agent never populates —
`actual_winner`, `actual_home_score`, `actual_away_score`,
`vanilla_llm_winner`, `vanilla_llm_confidence`, `statsinsider_home_prob`,
`notes` — reserved for the manual half of the evaluation. Because existing lines
are never rewritten, values typed into earlier rows survive every later run.

Both are written once per run, on every exit path. A run that dies resolving the
fixture still leaves a row saying it failed: a prediction missing from the log is
indistinguishable from a round nobody ran, and that ambiguity is worse than a
recorded failure.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Read the ledger each time | The reason this ADR exists. Correct, complete, and unusable at the pace of a round |
| Extend `summary.md` instead | Prose cannot be summed across rounds |
| Rewrite the CSV from all records each run | Would erase the hand-typed columns, which is the one outcome that must never happen |
| Include the manual columns in a separate file | Two files to join by hand, for no gain over trailing empty columns in one |
| SQLite | Better for querying, worse for a human editing it in a spreadsheet — which is the actual workflow |
| Emit Brier per run | A single prediction has no Brier score; it needs the result, which arrives days later |

## Consequences

The log is the capstone dataset. Accuracy per round, reliability across the
window, and Brier for all three prediction methods are spreadsheet formulas over
one file, and each row links back to the run directory when a number needs
explaining.

Because the CSV is opened in append mode, a spreadsheet holding a lock on it can
make a run's log write fail. The failure is caught and logged rather than
allowed to lose the run, and `record.json` is written regardless, so a missing
row can be recovered from the run directory.

`record.json` is a projection, not a source of truth. Anything it omits — full
article bodies, tool timings, raw LLM messages — is still in the ledger beside
it, and the record links back to it.
