# ADR 0008: The verifier reads article bodies, not just headlines

## Status

Accepted. Indexed as DD-33 in `key_design_decisions.md`.

## Context

The verifier's first checklist item is "every injury, player name, quote or
team-list claim in the judgement traces to a research item in the ledger". The
abridged ledger it was given contained, for the research tool, only the item
count, the first eight **titles**, and the queries run. Article bodies were
omitted to keep the audit prompt small.

Player names almost never appear in a headline. They appear in the body. So the
verifier was being asked a question its evidence could not answer, and an LLM
asked to audit for hallucinations with no evidence does not answer "I cannot
tell" — it answers "hallucination".

Observed on the Titans v Cowboys run of 2026-08-03
(`20260803T090516Z-0de3e8f7`). The judge cited an injury list sourced from
zerotackle.com's match centre. The verifier replied:

> these player names and their specific injury statuses do not appear in any of
> the tool outputs provided in the ledger

They appeared in three separate articles the tool had already fetched. The
recalibration loop then did as instructed and deleted the claim, replacing a
sourced availability fact with "Zero Tackle tips the Cowboys" — a tipster's
opinion. The verifier made the run strictly worse.

## Decision

The audit packet carries the same evidence the judge saw: for up to 12 research
items, the title, source domain, publication date, and the first 900 characters
of the body excerpt. The overall prompt cap rises from 24,000 to 40,000
characters, which the bounded per-item budget keeps it under in practice.

The verifier prompt states that player and injury detail lives in the body text
and that flagging a correctly sourced fact is as damaging as missing a
fabricated one — because the recalibration loop acts on the finding either way.

Two further failures on the same run were direction errors rather than
inventions, so "do not invent facts" had nothing to say about either.

The judge read zerotackle's injury table, whose "expected return: Round 23"
column means the player is *back* this round, and reported those players as
missing. The judgement prompt now covers reading availability news for
direction, and the verifier checks it.

The judge also cited two home-favouring SHAP drivers as reasons the away side
would win. The cause was the label: the math tool returns
`positive_drivers` / `negative_drivers`, where "positive" means *pushes
P(home win) up*. An LLM reads "positive" as "supports my conclusion", and when
the model picks the away side the two readings point opposite ways. The
agent now renames the groups to the club they favour before showing them to
either LLM — `favouring_Titans_home_win`, `favouring_Cowboys_away_win` — via
`label_shap_drivers()`, used by both the judgement packet and the audit packet
so the two always read the same evidence the same way. The math tool's own
output is unchanged, since other consumers depend on its contract.

## Alternatives considered

| Option | Why rejected |
| --- | --- |
| Keep titles only, soften the rule to "check what you can" | The rule is the verifier's main purpose; a verifier that cannot check grounding is theatre |
| Send the full research payload | Ten full articles plus SHAP and scene runs to ~80k characters, and the judge's own packet is already 15k; the bounded excerpt is what the judge reasoned from anyway |
| Make grounding a deterministic check instead | Matching free-text claims to source text is exactly the fuzzy-matching task an LLM is good at and a regex is not; the coded checks in ADR 0006 cover the rules that *are* decidable |
| Drop the recalibration loop so bad findings do no harm | Loses the loop's real value; the fix is to make findings trustworthy |

## Consequences

The audit prompt roughly triples in size, adding perhaps 30 seconds per run on
local Ollama. That is a fair price for a verifier that can distinguish a
fabricated injury from a real one.

This is the second time a component has been caught confidently asserting
something it had no evidence for (see ADR 0006 on the judge and weather). The
pattern worth carrying forward: before trusting any LLM check, confirm the
evidence needed to perform it is actually in its context window. Neither failure
was visible in the final answer — both needed the ledger to catch.
