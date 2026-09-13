# ADR 0004: Verifier recalibrate without re-tools

## Status

Accepted

## Context

The agent may overweight weak factors or cite unsupported claims. Re-running
scrapers is expensive and does not fix reasoning errors.

## Decision

Verifier = **deterministic checklist** + **LLM audit** (read-only on ledger).

On failure (max once): append a short instruction to the **same judgement chat
session**; orchestrator re-outputs a refined prediction. **No** new scene /
research / math calls. Orchestrator may agree or disagree with feedback.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Verifier re-runs full pipeline | Wasteful; conflates facts with reasoning |
| Checklist only | Misses overweight / hallucination patterns |
| LLM verifier only | Non-deterministic gates alone |

## Consequences

Clear SE story: measured research refine vs reasoning recalibrate. Both loops
ledgered independently (`MAX_RESEARCH_LOOPS=1`, `MAX_VERIFIER_LOOPS=1`).
