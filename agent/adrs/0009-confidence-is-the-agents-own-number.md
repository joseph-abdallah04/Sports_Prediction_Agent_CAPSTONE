# ADR 0009: Confidence is the agent's own number

## Status

Accepted. Supersedes the confidence rule in ADR 0006. Indexed as DD-41 in
`key_design_decisions.md`.

## Context

ADR 0006 required the judge's confidence to sit within 0.10 of the calibrated
model probability for the side it picked, with a 0.60 ceiling when picking
against the model. As a way to stop an LLM claiming 0.95 on a coin-flip fixture,
it worked.

As a way to *measure* anything, it is fatal. The Brier score of a prediction is a
function of its probability. If the agent's probability is constrained to within
0.10 of the model's, then the agent's Brier score is a near-copy of the model's
by construction — on the fixtures where the two agree, which is most of them, the
numbers are almost the same number. The comparative evaluation would then report
"the agent's probabilistic reliability was indistinguishable from the
deterministic tool's" as though it were a finding, when it was a consequence of
the prompt.

The research question asks whether the semantic layer improves *reliability*, not
only which side wins. A constraint that makes the reliability metric
uninformative removes the answer.

## Decision

The judge states its own confidence. Nothing compares it to the model
probability — not the prompt, not the checklist, not the LLM audit.

Overconfidence is addressed by giving the number a meaning and a reference class
drawn from the sport, rather than from our own model:

| Device | What it does |
| --- | --- |
| Frequency framing | "If you say 0.70 on a hundred fixtures like this one, your pick should win about seventy of them" — makes the number a claim rather than a mood |
| Explicit bands | 0.50-0.55 even, 0.55-0.65 modest edge (most fixtures), 0.65-0.75 clear edge, 0.75-0.85 rare, above 0.85 never. A small local model follows a rubric far more reliably than an abstraction like "be reasonable" |
| Pre-mortem | Name the strongest reason the pick could lose *before* choosing a number; if it is credible and unresolved, stay at or below 0.65 |
| Stated reasoning | The summary must say what set the confidence where it is, which the verifier checks — without reference to the model |

Two bounds remain in code, neither derived from the model:

| Bound | Why |
| --- | --- |
| `confidence >= 0.50` | Definitional, not calibration. Confidence is in the side the judge picked, so a lower number contradicts its own `winner`, and `_home_win_probability` would silently convert it into a pick for the *other* side — corrupting a scored row in a way nobody would notice |
| `confidence <= 0.95` | A backstop against a degenerate output, well outside the band the prompt asks for |

The model probability stays in the packet as evidence and is recorded separately
in `record.json` and the log, so the agent and the tool are scored independently
and the gap between them is itself an observation.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Keep the anchor | Makes the Brier comparison circular; the study's central metric would measure the prompt, not the system |
| Widen the anchor to 0.20 | Same defect, weaker. An arbitrary band is still a band |
| Record an unanchored confidence alongside an anchored official one | Two confidences invites reporting whichever looks better, and the official number would still be the circular one |
| Post-hoc recalibration of agent confidence | Needs far more than a five-round window to fit, and would be fitted on the same data it is evaluated on |
| No bounds at all | The 0.50 floor is a data-integrity guard, not a calibration rule; without it a scored row can silently contradict itself |

## Consequences

The agent's Brier score becomes an independent measurement, free to be worse
than the model's. That is the point: a comparison that cannot come out badly is
not a comparison. Expect the agent's calibration to be the weaker half of the
result, and report it honestly.

Because the bands are prompt-level guidance rather than enforced ceilings, a
local model may drift above them. That drift is visible — the confidence and the
model probability sit side by side in every record — so it can be reported as a
finding about LLM calibration rather than hidden by a clamp.

The bands themselves are asserted from the general character of the competition
rather than measured from our holdout. Deriving them from observed win rates per
probability bucket would make them empirical, and is the obvious refinement if
the calibration result turns out to matter.
