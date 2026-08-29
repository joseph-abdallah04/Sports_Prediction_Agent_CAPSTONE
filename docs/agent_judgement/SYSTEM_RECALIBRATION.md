# System recalibration (after Round 25)

This is the agreed fix list from the Round 23–25 audit in [`FINDINGS_AFTER_ROUND25.md`](FINDINGS_AFTER_ROUND25.md). It is a patch on a pipeline that already runs, not a rewrite.

What we expect on every run from Round 26 on is in [`EXPECTED_BEHAVIOUR.md`](EXPECTED_BEHAVIOUR.md).

Not in this round of changes:

- **No kickoff block.** Games can still be run inside an hour of (or after) kickoff. Live blogs are downranked in research instead. Try to run earlier when you can.
- **No change to the confidence bands.** The prompt still says 0.50–0.85, with 0.75–0.85 rare and “above 0.85 do not use.” Code now **enforces 0.85**, matching that prompt. We are not lowering the cap to 0.75.
- **No fill of `actual_winner`.** Empty CSV result columns did not affect predictions. Scoring stays a separate, after-the-fact step (your Google Doc, or later a lake/harness score command).
- **No XGBoost retrain** on 24 games.
- **No extra LLM loop** and the verifier still does not pick a winner.

---

## What we are aiming at

From the findings, four numbers to beat on the next rounds:

| Metric | R23–R25 |
|---|---|
| Research refine fired | 0/24 |
| Verifier audit pass | 1/24 |
| Verifier pick/confidence change | 0/23 recalibrations |
| Agent Brier | 0.256 (worse than always 0.50) |
| Confidence ≥ 0.70 hit rate | 7/13 (54%) |

The agent’s 15/24 side accuracy was fine. The problems were **noisy research**, **coin-flip math labels**, a **ceremonial verifier**, and **confidence the prompt already forbade**.

---

## Fix 1 — Clean the research pack

**Finding:** Research plumbing worked (15–21 items, official sources always present) but rank 1–2 was often someone else’s Late Mail, a January Casualty Ward URL (24/24 runs), other clubs’ team lists, and other-game Before You Bet pages. The refine gate never fired because “≥3 bodies + any injury keyword” is always true of a round wrap.

**Code:** `tools/qualitative_research/research/filter.py`, `assemble.py`; `agent/src/agent_app/research_gate.py`

| Change | What it does |
|---|---|
| Stop boosting league-wide Late Mail/Casualty/Team Lists by +2.5 | Club pages that name **both** fixture teams outrank a round wrap that names neither |
| Injury/team-list title bonus only if the article mentions a fixture team | Stops a Rabbitohs Late Mail headline beating a Titans–Cowboys club list |
| After bodies are fetched, drop roundups that still mention neither club | Sharks Late Mail inside Eels vs Cowboys |
| Drop the evergreen Casualty Ward URL (`…/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/`) | That URL was kept in every run |
| Downrank `live blog` / `as it happened` / `live scores` | Storm (after kickoff), Sharks R24, Titans R25 had live titles; we still allow the run |
| Drop titles that are clearly **another** known pairing (`Broncos vs Warriors Tips` in an Eels packet) | Other-game BYB pages were surviving as “round roundups” |
| Keep at most **2** league-wide roundups in the final list | Rest of the pack should be this fixture |
| Gate: ≥3 items whose text mentions **both** teams, and ≥1 of those is availability for **this** fixture | Refine can actually fire |

League Late Mail is not deleted. If the body names both clubs, it can still be kept — it just cannot dominate the list by default.

---

## Fix 2 — Put odds where the judge and verifier both see them

**Finding:** 11/24 verifier `sourced_claims` fails were `$1.32` / `$1.52` style prices. Those prices usually existed in the full article. `extract_market_mentions` scanned the full body; the verifier only saw the first 800 characters. Other-game tips also injected foreign `$` into the packet. Only Warriors–Panthers kept `$1.60` in the final JSON.

**Code:** `agent/src/agent_app/judgement.py`, `verifier.py`

- Only keep `$x.xx` from articles that mention **both** fixture teams.
- Attach a short **quote around the dollar amount** on the slim research item (judge) and on the verifier snip.
- Market is still an external prior to compare against, not to copy.

---

## Fix 3 — Stop presenting a coin-flip as a “Home Win”

**Finding:** Math labelled Titans–Cowboys 50.6%, Warriors–Panthers 53.0%, Raiders–Knights 54.9% as **Home Win** while `attribution_balance` leaned away. The judge treated SHAP totals as a second, better pick. Two of those flips were correct after the fact (Cowboys, Knights); Warriors–Panthers was wrong (Panthers @ 0.60, Warriors won 28–12). The prompt currently tells the judge that if balance `leans` away, “the maths is against you.”

**Code:** `tools/mathematical_engine/model/explain.py`; `agent/src/agent_app/prompts/__init__.py`

- If P(home) is between **0.45 and 0.55** inclusive, the hard label is **Too close**, not Home/Away Win. `home_win_probability` stays the prior.
- `attribution_balance` note: this is SHAP mass, **not a second prediction**.
- Judge may only pick against a Home Win / Away Win label when **research** gives a named availability or form fact. Ladder, H2H, venue history, SHAP `leans`, and bookie prices are not enough on their own.

Eels vs Cowboys (H2H/venue override of ratings) is the same class of error; the prompt change covers it. That pick happened to win 32–30.

---

## Fix 4 — Verifier only chases large SHAP drivers

**Finding:** Checklist 24/24 pass. LLM audit 1/24 pass. Recalibration 23/24. Winner and confidence never changed. Almost every fail was `omitted_math_signals` on padded five-item lists (1–2% CONFLICT rows, “home travel 0 km”). Recalibration pasted SHAP names into the summary and kept Roosters @ 0.83.

**Code:** `agent/src/agent_app/verifier.py`, `prompts/__init__.py`

- `omitted_math_signals` only requires drivers at **≥ 8% of total SHAP** (Elo, Bradley-Terry, ladder). Tiny padded rows are ignored.
- The audit packet lists those material drivers explicitly.
- If the **only** audit fail is that coverage check, **skip recalibration**. Recalibration still runs for invented injuries, wrong availability direction, weather as headline, unsourced `$`, or confidence out of bounds.

---

## Fix 5 — Enforce the existing 0.85 ceiling in code

**Finding:** Prompt already says “above 0.85 do not use.” Code allowed **0.95**. Roosters vs Tigers went **0.83 with Tedesco out** (inside the prompt’s rare band, still a Brier disaster). The 0.70+ band hit 54%.

**Code:** `agent/src/agent_app/verifier.py` `CONFIDENCE_CEILING`

- Ceiling is **0.85**, the prompt’s own maximum. Not 0.75, not 0.95.
- Floor stays 0.50 (below that, the judge has contradicted its own winner).
- A 0.86+ judgement fails the checklist and forces one recalibration.

The Round 25 plan said we would **not** compare confidence to the math probability (so the agent’s Brier would not just copy the model). Throwaway tests then showed the judge *was* copying the model’s number anyway. Fix 6 is the process rule for that, without turning confidence into “always equal math P.”

---

## Fix 6 — Confidence is P(the pick wins), not a pasted math number

**Finding (R23–R25):** The prompt already said confidence is the probability the picked side wins. In practice the judge often rounded `home_win_probability` to two decimals and called that confidence. High-confidence picks (≥0.70) were only right **7/13** times. The worst case was Roosters vs Tigers @ **0.83** with Tedesco out.

**Finding (throwaway R26 tests, 25 Aug 2026, not in the official log):**

| Run | Pick | Confidence | What happened |
|---|---|---|---|
| Broncos vs Storm (morning) | Storm | **0.61** | Exact copy of math P(away)≈0.6108. Published research was “neither team makes finals.” Hughes named at 7 was in the pack and left out of the verdict. |
| Sea Eagles vs Dragons | Sea Eagles | **0.75** | Copied math 0.7499, but research really did support it (Trbojevic back, Feledy hat-trick). Same side as math is fine; the number happened to match. |
| Broncos vs Storm (evening, after first confidence patch) | Storm | **0.68** | Stopped pasting 0.61. Used Hughes as `confirms`, then **climbed a band** by counting math + ladder + SHAP as three signals. Named Suncorp as a reason it could lose, then ignored the ≤0.65 rule. |

We want the judge to **use** research, and we allow the same side as math. Research can move confidence **down or up**. **Going less sure than the math prior is the usual move**. **Going more sure is the rare exception:** only when the news is a real this-week shock the ratings could not have known. We do **not** hard-code a list of shocks. “I found an article, so add 7%” is the failure mode. Keeping or raising the math number while research **conflicts** is also a failure.

**29 Aug 2026:** the first Fix 6 pass also forced ≤ 0.65 whenever `loss_reason_specific` was true (and for `conflicts`). That flattened official R26 picks onto 0.65. That cap is **removed**. The agent must still *use* a genuine loss reason; it chooses the number. Bands remain descriptive.

**Code / prompt:** `agent/src/agent_app/prompts/__init__.py`, `judgement.py`, `verifier.py`, `record.py`, `report.py`

| Rule | What it means in the report | How it is enforced |
|---|---|---|
| Confidence = P(pick wins) | The output number is a frequency claim, not a vibe | Prompt + verifier `confidence_justified` |
| `research_stance` | `confirms` / `conflicts` / `mixed` / `silent`, from **articles**, not from how big the math number is | Required JSON field. `confirms` is rejected if the research key factor is only stakes/ladder (“neither in finals”), not this-fixture team news |
| Same side as math is allowed | The agent may agree with the model | Prompt. No code that forces a flip |
| Pasting math P is not allowed unless research really confirms | Morning Storm @ 0.61 would fail today | Checklist: two-decimal match to math P(the picked side) is rejected unless `confirms` is backed by team news |
| Ladder / SHAP / standings are **one** math signal | Evening Storm @ 0.68 counted them as three votes | Prompt only (“one math signal, not three”). Not a keyword ban |
| `confirms` is agreement, not a bonus | Finding a team list does not mean “add 0.07” | Prompt. Code does not freeze the number to math P |
| Getting surer than the prior is **rare** | Needs a real this-week shock the model could not know. We do **not** list allowed shocks | Prompt. Code does **not** require a particular kind of shock to climb |
| Getting less sure than the prior is **normal** | Mixed/silent news, or a genuine reason you could lose, should move the number down; how far is the judge’s call | Prompt. `conflicts` in code: must sit **below** math P (no forced 0.65) |
| `loss_reason_specific` | Named this-week fact that could beat the pick. Use it in the number. **Do not** force ≤ 0.65 | Required boolean. Checklist no longer caps on this flag |
| Above 0.65 needs real `confirms` | Clear-edge band is not the default | Checklist |
| `conflicts` cannot keep or raise the math number | Tedesco-out @ 0.83 is the case this catches | Checklist (below prior, not a 0.65 landing) |

JSON the judge must now return (extra fields vs R23–R25): `research_stance`, `strongest_reason_could_lose`, `loss_reason_specific`. Those also appear on `summary.md` and in `record.json` under `reasoning`.

**What we deliberately did not do:** tell the agent who to pick; pin confidence to the math probability; forbid all band climbs; encode “only injuries count as a shock”; forbid coming **down** from the prior; force a landing score (0.65) when a loss reason is named.

---

## How this maps to the ranked findings

| Finding (severity) | Fix |
|---|---|
| 1. Calibration / overconfidence | 5 (0.85 ceiling) + 6 (don’t paste math P; come down when research conflicts; don’t climb on non-shocks) + 3 (fewer unjustified coin-flip flips) |
| 2. Research volume ≠ quality | 1 |
| 3. Verifier ceremonial | 4 |
| 4. Coin-flip math UX | 3 |
| 5. Odds grounding packet bug | 2 |
| 6. Late / live-blog runs | Live-blog downrank only; runs still allowed |
| 7. Scene/math wiring is a strength | Untouched |

---

## How to test before treating this as the new default

Do **not** commit until a real fixture run looks right.

1. Offline control loop (stubs, ~2 seconds):

   ```bash
   cd agent
   uv run python scripts/smoke_orchestrator.py
   ```

2. Filter / gate / odds / verifier helpers (no network, no Ollama):

   ```bash
   cd tools/qualitative_research && uv run python scripts/smoke_filter.py
   cd ../../agent && uv run python scripts/smoke_recalibration.py
   cd ../tools/mathematical_engine && uv run python scripts/smoke_too_close.py
   ```

3. One real game, same as usual, when you have a fixture:

   ```bash
   cd agent
   uv run python -m agent_app.cli --home HOME --away AWAY --season 2026 --round N --force-refresh
   ```

   Check in that run’s `summary.md` / `ledger.json`:

   - Top research items name **this** fixture’s clubs, not another game’s Late Mail.
   - The January Casualty Ward URL is absent.
   - If math P(home) is ~0.50, the label is **Too close**.
   - Verifier either passes or, if it only nags about small SHAP rows, **does not** recalibrate.
   - Confidence cannot land above 0.85.
   - `research_stance` and `loss_reason_specific` are present.
   - Confidence is not a two-decimal paste of math P unless research really confirms the pick.
   - A named this-week loss reason should move confidence; it must **not** force 0.65.

Throwaway R26 folders (`2026-R26_Broncos-v-Storm`, `2026-R26_Sea-Eagles-v-Dragons`) and extra CSV rows were for testing only and should not be treated as official Round 26 predictions.

Existing R23–R25 ledgers are historical. They will not be rewritten.
