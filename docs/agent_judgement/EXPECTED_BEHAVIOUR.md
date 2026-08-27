# What we expect from the agent (from Round 26 on)

This is the intended judgement behaviour. Watch every official run against it. Side accuracy (did the pick win?) is scored later. This file is about **whether the run thought correctly**.

Rounds 23–25 were the old system: see [`FINDINGS_AFTER_ROUND25.md`](FINDINGS_AFTER_ROUND25.md). The code changes are in [`SYSTEM_RECALIBRATION.md`](SYSTEM_RECALIBRATION.md). The first official example of this behaviour is Broncos vs Storm, 27 August 2026 (`20260827T045035Z`).

---

## The job in one sentence

Use the **math model as the starting number**. Then use **this week’s news** (what the ratings cannot see) to **agree or disagree**. Do not invent a second computer.

## What each tool is for

| Tool | What it is | What it is not |
|---|---|---|
| Math | The prior: P(home) / P(away), the Home / Away / Too close label, SHAP, ladder | Three extra votes. Ladder, SHAP, and standings are the **same** signal |
| Research | This-week facts the model cannot see: who is in, who is out, last home game, a named shock | A bonus for finding an article. “Neither team makes finals” is not confirmation |
| Scene | Kickoff, venue, weather, readable standings | A third reason to climb confidence |

## Agree vs disagree

**Agree** (news backs the math favourite): keep the same side. You may keep the prior. You may still come **down** if there is a named reason the pick could lose (venue, a player out for your side, last home game). Finding a team list is not a reason to go from 0.61 to 0.68.

**Disagree** (news cuts against the favourite): same side is still allowed, but confidence **must come down** (below the prior, and not above 0.65). Flip the side only if a concrete research fact actually supports the other team.

**Get surer than the prior:** rare. Needs a real this-week shock the ratings could not have known. We do not list allowed shocks. Do not climb by stacking math + ladder + SHAP.

## Confidence

Confidence is P(the picked side wins). It is not a vibe and not a pasted math number unless research really confirms.

- `confirms` — named team news on **this** fixture backs the pick. Agreement, not a bonus.
- `conflicts` — named team news cuts against the favourite. Come down.
- `mixed` / `silent` — same side is fine; do not paste the prior; stay at or below it unless that rare shock applies.
- If `loss_reason_specific` is true, stay at or below **0.65**.
- Hard ceiling **0.85**.

## What a good run looks like

Broncos vs Storm (official): math said Storm ~61%. News said Hughes is back (**agree**) and last home game at Suncorp (**reason it could lose**). Verdict: Storm **0.61**. Same side, same number, no climb.

A disagreeing run would look like Roosters vs Tigers with Tedesco out: do not keep 0.83.

## What to check on every new run

Read `summary.md` (and `thinking.md` if something looks off):

1. Is the math probability the **starting point**, not an afterthought?
2. Did research name a **this-fixture** fact (player in/out, not a round wrap about other clubs)?
3. If news **agrees**, did confidence stay at or below the prior unless there was a real shock?
4. If news **disagrees**, did confidence come **down**?
5. If the loss reason is a named this-week fact, is confidence ≤ 0.65?
6. Are ladder / SHAP / standings treated as one math signal, not three reasons to get surer?
7. Are published claims (who is in, who is out, ladder spots) actually in the tool output?

If a run fails this, say so plainly. Do not treat a correct final score as proof the logic was right, and do not treat a wrong score as proof the logic was wrong.
