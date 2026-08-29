# What we expect from the agent (from Round 26 on)

This is the intended judgement behaviour. Watch every official run against it. Side accuracy (did the pick win?) is scored later. This file is about **whether the run thought correctly**.

Rounds 23–25 were the old system: see [`FINDINGS_AFTER_ROUND25.md`](FINDINGS_AFTER_ROUND25.md). The code changes are in [`SYSTEM_RECALIBRATION.md`](SYSTEM_RECALIBRATION.md).

---

## The job in one sentence

Use the **math model as the starting number**. Then use **this week’s news** (what the ratings cannot see) to **agree or disagree**. Do not invent a second computer. The agent chooses the confidence number; we do not tell it to land on 0.65.

## What each tool is for

| Tool | What it is | What it is not |
|---|---|---|
| Math | The prior: P(home) / P(away), the Home / Away / Too close label, SHAP, ladder | Three extra votes. Ladder, SHAP, and standings are the **same** signal |
| Research | This-week facts the model cannot see: who is in, who is out, last home game, a named shock | A bonus for finding an article. “Neither team makes finals” is not confirmation |
| Scene | Kickoff, venue, weather, readable standings | A third reason to climb confidence |

## Agree vs disagree

**Agree** (news backs the math favourite): keep the same side. You may keep the prior. Finding a team list is not a reason to climb. If there is also a genuine this-week reason the pick could lose, fold that into the number — how far is the agent’s call.

**Disagree** (news cuts against the favourite): same side is still allowed, but confidence **must come down from the prior**. How far is the agent’s call. Flip the side only if a concrete research fact actually supports the other team.

**Get surer than the prior:** rare. Needs a real this-week shock the ratings could not have known. We do not list allowed shocks. Do not climb by stacking math + ladder + SHAP.

## Confidence

Confidence is P(the picked side wins). It is not a vibe, not a pasted math number unless research really confirms, and **not a required landing score**.

The bands say where a number *belongs*. They are not a cap we force:

- 0.50–0.55 evenly matched, or evidence points both ways
- 0.55–0.65 a modest edge (including a math prior around 0.60)
- 0.65–0.75 a clear edge: usually because the math prior is already here **and** research confirms
- 0.75–0.85 rare
- Hard ceiling **0.85** (enforced in code)

- `confirms` — named team news on **this** fixture backs the pick. Agreement, not a bonus. You may keep a 0.70–0.75 prior.
- `conflicts` — named team news cuts against the favourite. Come down from the prior; do not keep 0.83.
- `mixed` / `silent` — same side is fine; do not paste the prior; stay at or below it unless that rare shock applies.
- `loss_reason_specific` — a named this-week fact that could beat the pick. **Use it.** Do not flatten every such game to 0.65.

## What a good run looks like

Broncos vs Storm (official): math said Storm ~61%. News said Hughes is back (**agree**) and last home game at Suncorp (**reason it could lose**). Verdict: Storm **0.61**. Same side, no climb.

A disagreeing run would look like Roosters vs Tigers with Tedesco out: do not keep 0.83. The agent decides the new number.

Cowboys with Dearden/Nanai back and a 0.72 prior should be allowed to **keep** a clear-edge number if the only “risk” is last week’s already-modelled result. That is not a 0.65 job.

## What to check on every new run

Read `summary.md` (and `thinking.md` if something looks off):

1. Is the math probability the **starting point**, not an afterthought?
2. Did research name a **this-fixture** fact (player in/out, not a round wrap about other clubs)?
3. If news **agrees**, did confidence stay at or below the prior unless there was a real shock? A high prior with real `confirms` may stay in 0.65–0.75.
4. If news **disagrees**, did confidence come **down from the prior** (not necessarily to 0.65)?
5. If there is a genuine this-week reason the pick could lose, is it reflected in the number — without being a forced cap?
6. Are ladder / SHAP / standings treated as one math signal, not three reasons to get surer?
7. Are published claims (who is in, who is out, ladder spots) actually in the tool output?

If a run fails this, say so plainly. Do not treat a correct final score as proof the logic was right, and do not treat a wrong score as proof the logic was wrong.
