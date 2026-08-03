# ADR 0006: Grounded judgement and anchored confidence

## Status

Accepted. Indexed as DD-31 in `key_design_decisions.md`.

## Context

Reviewing early runs surfaced three recurring faults in the judgement session,
all of them plausible-sounding and therefore easy to miss:

1. **Weather inflation.** The judge repeatedly named match-day weather as a key
   factor. The scene tool reports weather, so it is right there in the packet —
   but `ctx_weather` is missing in ~36% of training matches and does not appear
   in the model's top SHAP drivers. The judge was dressing up a non-signal.
2. **Research ignored.** Research items were retrieved, summarised into the
   packet, and then not cited at all; the judgement effectively restated the
   math model. The qualitative half of the system was doing no work.
3. **Unanchored confidence.** Confidence was whatever number the LLM felt like,
   with no relationship to the calibrated probability it had been handed.

The prompt already said "do not invent facts", which does not address any of
these — none of them is an invention, they are misweightings.

## Decision

Three rules, each stated in the prompt **and** enforced in code where the
ledger makes them decidable:

| Rule | Prompt | Coded check in `verifier.py` |
| --- | --- | --- |
| Weather is not a key factor unless a weather feature is in the SHAP drivers | yes | `weather_cited_without_shap_support` |
| At least one key factor must come from research when research returned items | yes | `no_research_key_factor_despite_items` |
| Confidence within 0.10 of the model probability for the picked side; ceiling 0.85; ceiling 0.60 when picking against the model | yes | `confidence_detached_from_model`, `confidence_above_ceiling` |

Failures feed the existing in-session recalibration loop (ADR 0004), so the
judge gets one chance to answer them before the run finishes.

The prompt also states the model's measured performance (~63% accuracy, ~0.65
AUC on unseen seasons) so the LLM has a calibration reference rather than an
intuition.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Prompt instructions only | The verifier LLM is as fallible as the judge; these rules are decidable from the ledger, so a coded check is strictly better |
| Drop `ctx_weather` from the model | Weather plausibly interacts with completion rate and kicking game; the problem is the judge's weighting, not the feature's presence (see DD-13) |
| Compute confidence directly from the model and skip the LLM | Then research can never move the number, which defeats the point of the qualitative half |
| Hard-fail the run on violation | Too brittle for a weekly demo; recalibration plus a ledgered issue is the honest middle |

## Consequences

Confidence becomes an auditable number rather than a vibe: any value can be
checked against `home_win_probability` in the ledger. The judge can still
disagree with the model, but disagreement is capped and must be explained in
`disagreements_with_math`.

The cost is that genuinely decisive qualitative news — a late scratching of a
key half, say — cannot push confidence more than 0.10 past the model. That is
deliberate for now: the agent has no way to quantify a player's absence, so a
large deviation would be false precision. Revisit if lineup-strength features
ever enter the model.
