# Limitations and future work

An honest account of what this system cannot do, why, and what it would take
to change. Every number here is measured on the untouched 2025–2026 holdout
(376 matches) or taken from a run ledger, not estimated.

Related reading: [`key_design_decisions.md`](key_design_decisions.md) for the
decisions themselves, [`agent/adrs/`](agent/adrs/) for the agent's design
records, and [`tools/mathematical_engine/Data_Quality_Findings.md`](tools/mathematical_engine/Data_Quality_Findings.md)
for data defects found during ETL.

---

## 1. How accurate is it, really

| Predictor | Accuracy | AUC | Log loss |
| --- | --- | --- | --- |
| Always back the home team | 56.7% | — | — |
| Base rate (predict 0.564 every time) | — | 0.500 | 0.684 |
| **This model (2025–2026 holdout)** | **63.0%** | **0.656** | **0.649** |

Published NRL and AFL match-prediction models generally land between 0.60 and
0.67 AUC, so this sits inside the normal band rather than above it. The +6.3
accuracy points over always-backing-the-home-team is the honest measure of what
the modelling adds.

### The model knows what it does not know

Accuracy broken down by the model's own confidence, holdout, averaged over 8
seeds:

| Model confidence | Share of games | Actual accuracy |
| --- | --- | --- |
| 0.50 – 0.55 | 20.7% | 53.8% |
| 0.55 – 0.60 | 15.4% | 58.6% |
| 0.60 – 0.65 | 17.6% | 59.1% |
| 0.65 – 0.70 | 16.0% | 66.7% |
| 0.70 + | 30.3% | 71.9% |

Predicted confidence tracks realised accuracy closely at every level. That is
the property that matters most for this project: when the model says 52% it
really is a coin flip, and when it says 75% it is right about 72% of the time.
A model that was wrong *and* confident would be far more dangerous than one that
is modestly accurate and honest.

These are also the numbers behind the confidence bands the agent is asked to work
in (ADR 0009). Note the top row: nothing the model produces realises much above
72%, which is why the prompt treats 0.75–0.85 as rare and forbids anything above
0.85. The agent is free to exceed the model — it sees team news the model cannot
— but a confidence the *sport* does not support is overconfidence regardless of
where it came from.

The agent's own confidence is deliberately **not** anchored to this number
(DD-41). Anchoring produced better-looking calibration at the cost of making the
Brier comparison circular, and a metric that cannot come out badly measures
nothing. Expect the agent's calibration to be the weaker half of the results, and
report the gap between its confidence and `math_home_win_prob` rather than
hiding it.

It also shows where the accuracy actually goes: **over a third of NRL matches
are near coin flips** on these features. The system is not failing on those
games so much as correctly reporting that they are unpredictable from
form, ratings and ladder position alone.

---

## 2. Can it reach 70%?

Short answer: not with public pre-match data of this kind, and not by adding
more history. 65–67% is a realistic stretch; 70% is roughly bookmaker
territory.

### More data will not do it — this is measured, not assumed

Holdout AUC when the model is trained on progressively more history, 6 seeds
each:

| Training window | Matches | Holdout AUC |
| --- | --- | --- |
| 2021–2024 | 823 | 0.654 ± 0.002 |
| 2019–2024 | 1,189 | 0.652 ± 0.004 |
| 2017–2024 | 1,590 | 0.660 ± 0.002 |
| 2015–2024 | 1,990 | 0.655 ± 0.003 |

The curve is flat. Quadrupling the training data moves AUC by less than the
seed-to-seed noise. Backfilling 2010–2014 would add roughly 800 matches to a
curve that has already plateaued, so it is not worth the ETL effort. **The
bottleneck is signal, not sample size.**

### What would actually move it

| Lever | Expected effect | Cost / risk |
| --- | --- | --- |
| **Team lineup strength** — who is actually named, weighted by player quality, especially halves and fullback | The largest missing signal. Bookmakers price late outs heavily, and this system currently has none of it in the model | Needs a player-rating layer and reliable pre-match team lists; the research tool already *finds* this news, it just cannot quantify it |
| Market odds as a feature | Would lift accuracy quickly | Self-defeating for a Capstone: the model would mostly be learning to copy the bookmaker, and could never be evaluated as an independent predictor |
| In-play / contextual state (travel fatigue interactions, coaching changes, motivation) | Small, uncertain | Hard to encode without leakage; the ladder and short-turnaround features already proxy part of it |
| A margin model alongside win probability | No accuracy gain on the win label, but richer output | Moderate; useful for the report, not for accuracy |
| More rolling-form variants | Near zero | Already 42 such features; SHAP shows sharp diminishing returns past the top few |

The ranking is deliberate. Everything except lineup strength is polish.

### Why 70% is the wrong target

Rugby league is high-variance: an 82–12 result (Roosters over Cowboys, round 22
2026) sits in the same dataset as a one-point game. The betting market — with
lineup data, injury intelligence, insider information and vastly more
modelling resource — is the practical ceiling, and it is not at 90%. Chasing
70% on public data would mean overfitting the holdout until it *reported* 70%,
which is exactly the failure mode this project's A/B protocol (DD-30) exists to
prevent.

---

## 3. Limitations of the agent

**The agent cannot be backtested.** The research channels return *today's*
news. There is no honest way to reconstruct what was knowable before a 2023
kickoff, so historical agent backtests would be leak-ridden fiction. The math
model can be evaluated over years; the agent can only be measured forward, one
round at a time (DD-32). Every agent number in this project will therefore be
small-sample, and the harness prints `n` beside each metric so that is visible.

**The LLM is the least reliable component.** Three separate failures were found
by reading ledgers, none visible in the final answer:

- inflating match-day weather into a headline factor when SHAP ranked it
  nowhere (ADR 0006);
- reading an injury table's "expected return: round 23" as *out* when it means
  *back*, and citing home-favouring SHAP drivers as reasons the away side would
  win (ADR 0008);
- the verifier declaring a correctly sourced injury list a hallucination
  because it had been shown only headlines, then the recalibration loop
  deleting a true fact (ADR 0008).

Each is now addressed, but the pattern is the point: **an LLM asked to check
something it lacks the evidence for will answer confidently rather than
abstain.** Wherever a rule is decidable from the ledger it is enforced in code,
not requested in a prompt.

**Research recall is bounded by what is public and free.** Fox Sports, the
Daily Telegraph and The Australian sit behind a redirect to a tracking domain
that a DNS blocker refuses, so their article bodies frequently cannot be
fetched and only the search snippet survives. Reddit's search endpoint is
blocked to unauthenticated clients entirely, and its channel is off by default
(DD-34). Typical yield is 10–15 usable items per fixture from nrl.com, Google
News RSS and DuckDuckGo.

**Relevance filtering is heuristic, and its errors are quiet.** Roughly half
the NRL's club nicknames are shared with teams in other codes, so a keyword
search for "Titans" returns the Tennessee Titans and a *Remember the Titans*
retrospective alongside the Gold Coast. Requiring positive evidence of rugby
league rather than blacklisting other sports (DD-37) removes the collisions
seen so far, but the filter is a set of rules over titles and bodies, not a
classifier: every dropped item is logged with its reason precisely because the
only way to catch a wrongly dropped article is to read that log.

**Qualitative evidence cannot move the number much.** Confidence is capped at
0.10 from the model probability (DD-31). A genuinely decisive late scratching
therefore cannot swing the prediction the way it should. This is deliberate —
the agent has no way to quantify a player's absence, so a larger deviation
would be false precision — but it does mean the qualitative half is currently
worth less than it could be. Lineup-strength features in the model are the
prerequisite for relaxing it.

**Local inference is slow.** A full run on `gemma4:31b` takes 8–10 minutes,
almost entirely in the judgement and verifier calls. A round of eight fixtures
is roughly an hour. A hosted provider removes this, at the cost of an API key
(see `config.toml`).

---

## 4. Data limitations

- **Weather is missing for ~36% of matches** and is kept as an explicit
  `unknown` category rather than imputed (DD-13). The model finds it close to
  irrelevant either way.
- **Detailed match statistics begin in 2019.** Pre-2019 rows carry NaNs for the
  richer rolling-form features; XGBoost routes them natively rather than having
  values invented for them.
- **Draws are excluded** (9 matches) because the label is binary. In a season
  they are rare enough not to matter for training, but the harness has to
  exclude and count them at scoring time rather than pretend they were losses.
- **Venue geography is a hardcoded table** (DD-09). A brand-new venue silently
  defaults to no-travel until someone adds its coordinates — which happened
  once already, with One NZ Stadium in 2026.

---

## 5. If this work continued

In priority order, by expected value rather than by ease:

1. **Player availability as a model feature.** Convert the team lists the scene
   tool already retrieves into a lineup-strength differential. This is the only
   change on this list with a realistic shot at a material accuracy gain, and it
   would also let the confidence cap be relaxed.
2. **More forward-measured rounds.** One round is an anecdote. Ten rounds of
   harness output would say something real about whether the agent beats the
   model it wraps.
3. **A margin model** alongside win probability, for richer output and a second
   evaluation axis.
4. **Structured extraction from research** — parse "OUT: X, IN: Y" from Late
   Mail into fields rather than leaving the LLM to read prose. Would remove the
   direction errors described above at the source instead of guarding against
   them.
