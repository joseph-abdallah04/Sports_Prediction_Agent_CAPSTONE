# Findings after Round 25

A read-only audit of the 24 canonical Round 23–25 prediction runs. Written 25 August 2026. No files were changed as part of the audit itself.

This is the full write-up: what worked, what did not, and every number and example the audit produced. Plain language, nothing left out. The fixes are in [`SYSTEM_RECALIBRATION.md`](SYSTEM_RECALIBRATION.md). What we expect from Round 26 on is in [`EXPECTED_BEHAVIOUR.md`](EXPECTED_BEHAVIOUR.md).

---

## What was audited

- The **24 games** in `agent_runs/predictions_log.csv` (8 per round, Rounds 23–25).
- Each run’s `ledger.json`, `record.json`, `summary.md`, and `thinking.md`.
- How the three tools behaved: **scene** (fixture facts), **research** (news), **math** (model + SHAP).
- How the **judge** (the LLM that picks a winner) used that information.
- How the **verifier** (checklist + second LLM pass) behaved after the pick.
- Actual scores, taken from the data lake after the weekly ETL on 24 August 2026. The CSV columns `actual_winner` / `actual_home_score` / `actual_away_score` are still empty. The scoring harness has not been used yet. These results were matched by hand from scraped match JSON.

Out of scope:

- `agent_runs/archive/` (early development / smoke runs).
- The Titans vs Cowboys folder named `OLD TEST`.

---

## Headline

The pipeline **works**. Scene, math, research, query planning, judgement, and verifier all fire, write ledgers, and finish.

The agent is **decent at picking a side** (15/24, one better than the math model) and **weak at putting the right weight on that information** — especially confidence, coin-flip overrides, and noisy research.

Tools are **operationally healthy** and **only partly useful as a briefing for that specific game**. The judge is **fluent and usually grounded**, but it does not reliably treat the math probability as the starting point on hard calls. The verifier almost never changes a decision.

---

## Score against what actually happened

Home teams only won **9/24 (37.5%)** in this stretch. That is an away-heavy sample. “Always pick the home team” would have been terrible.

| System | Correct sides | Brier (lower is better) |
|---|---|---|
| Agent | **15/24 (62.5%)** | 0.256 |
| Math model | 14/24 (58.3%) | 0.270 |
| Always 50/50 | — | **0.250** |

Brier is a scoring rule for probabilities: if you say 0.80 and lose, you are punished harder than if you said 0.55 and lose. The agent beat the model by **one extra correct pick**. It did **not** beat a coin-flip Brier. High-confidence misses are the problem, not the winner column.

By round:

- Round 23: agent 6/8, math 5/8
- Round 24: both 4/8
- Round 25: both 5/8

### Every game

Format: agent pick @ confidence → actual score. Math pick in brackets if it differed.

**Round 23**

| Game | Agent | Math P(home) | Actual | Agent | Math |
|---|---|---|---|---|---|
| Titans v Cowboys | Cowboys @ 0.58 (flipped) | Titans 0.506 | Cowboys 8–30 | Correct | Wrong |
| Warriors v Panthers | Panthers @ 0.60 (flipped) | Warriors 0.530 | Warriors 28–12 | Wrong | Correct |
| Roosters v Bulldogs | Roosters @ 0.70 | Roosters 0.740 | Roosters 20–18 | Correct | Correct |
| Storm v Sea Eagles | Storm @ 0.57 | Storm 0.558 | Storm 42–20 | Correct | Correct |
| Dolphins v Broncos | Dolphins @ 0.74 | Dolphins 0.743 | Dolphins 40–32 | Correct | Correct |
| Rabbitohs v Eels | Rabbitohs @ 0.70 | Rabbitohs 0.698 | Rabbitohs 28–24 | Correct | Correct |
| Raiders v Knights | Knights @ 0.60 (flipped) | Raiders 0.549 | Knights 24–30 | Correct | Wrong |
| Dragons v Sharks | Sharks @ 0.74 | Sharks 0.265 | Dragons 24–16 | Wrong | Wrong |

**Round 24**

| Game | Agent | Math P(home) | Actual | Agent | Math |
|---|---|---|---|---|---|
| Panthers v Roosters | Panthers @ 0.60 | Panthers 0.660 | Roosters 6–12 | Wrong | Wrong |
| Sea Eagles v Dolphins | Dolphins @ 0.68 | Dolphins 0.489 | Dolphins 0–22 | Correct | Correct |
| Bulldogs v Rabbitohs | Bulldogs @ 0.71 | Bulldogs 0.738 | Rabbitohs 6–22 | Wrong | Wrong |
| Sharks v Raiders | Sharks @ 0.72 | Sharks 0.785 | Raiders 20–24 | Wrong | Wrong |
| Eels v Cowboys | Eels @ 0.56 | Eels 0.563 | Eels 32–30 | Correct | Correct |
| Broncos v Warriors | Warriors @ 0.72 | Warriors 0.321 | Warriors 6–40 | Correct | Correct |
| Knights v Titans | Knights @ 0.74 | Knights 0.738 | Knights 36–26 | Correct | Correct |
| Wests Tigers v Dragons | Wests Tigers @ 0.60 | Wests Tigers 0.574 | Dragons 22–24 | Wrong | Wrong |

**Round 25**

| Game | Agent | Math P(home) | Actual | Agent | Math |
|---|---|---|---|---|---|
| Storm v Panthers | Panthers @ 0.60 | Panthers 0.403 | Panthers 14–22 | Correct | Correct |
| Raiders v Broncos | Raiders @ 0.72 | Raiders 0.709 | Broncos 30–34 | Wrong | Wrong |
| Dolphins v Eels | Dolphins @ 0.75 | Dolphins 0.833 | Dolphins 34–16 | Correct | Correct |
| Knights v Sea Eagles | Knights @ 0.70 | Knights 0.693 | Sea Eagles 24–44 | Wrong | Wrong |
| Rabbitohs v Warriors | Warriors @ 0.60 | Warriors 0.430 | Warriors 26–45 | Correct | Correct |
| Dragons v Bulldogs | Bulldogs @ 0.65 | Bulldogs 0.316 | Bulldogs 14–44 | Correct | Correct |
| Titans v Sharks | Sharks @ 0.73 | Sharks 0.270 | Sharks 22–30 | Correct | Correct |
| Roosters v Wests Tigers | Roosters @ 0.83 | Roosters 0.831 | Wests Tigers 24–25 | Wrong | Wrong |

### The three times the agent disagreed with math

| Game | Math | Agent | Actual | Who was right |
|---|---|---|---|---|
| Titans v Cowboys | Titans 50.6% | **Cowboys 0.58** | Cowboys 8–30 | Agent |
| Raiders v Knights | Raiders 54.9% | **Knights 0.60** | Knights 24–30 | Agent |
| Warriors v Panthers | Warriors 53.0% | **Panthers 0.60** | Warriors 28–12 | Math |

These were not random. In all three, the model’s hard label said **Home Win** while `attribution_balance` (the sum of SHAP drivers toward each side) leaned away. The judge treated that imbalance as “the real math.”

That is a reasonable reading of a confusing packet, and it happened to help twice. It is **not** “research adjusted a prior.” On Warriors vs Panthers the judge also leaned on ladder position and the market (`$1.60` is still in the final JSON).

### Eels vs Cowboys (Round 24)

This is the other reasoning case that stood out during the season.

The thinking trace did notice that the Cowboys were the market favourite and higher on the ladder. The judge then stuck with the Eels because of head-to-head (5 of the last 6) and CommBank Stadium (Cowboys 1 win in 5 visits). That was heavier on history/venue than the prompt wants. The result was Eels 32–30. The pick matched math and was correct.

### High-confidence misses (confidence 0.70 or higher)

13 picks sat at 0.70 or above. **6 of those 13 lost**. That is a **54% hit rate** in a band the prompt calls a “clear edge.”

| Game | Pick | Confidence | Actual |
|---|---|---|---|
| Dragons v Sharks R23 | Sharks | 0.74 | Dragons 24–16 |
| Bulldogs v Rabbitohs R24 | Bulldogs | 0.71 | Rabbitohs 6–22 |
| Sharks v Raiders R24 | Sharks | 0.72 | Raiders 20–24 |
| Raiders v Broncos R25 | Raiders | 0.72 | Broncos 30–34 |
| Knights v Sea Eagles R25 | Knights | 0.70 | Sea Eagles 24–44 |
| Roosters v Wests Tigers R25 | Roosters | **0.83** | Tigers 24–25 |

The worst of those is **Roosters vs Tigers @ 0.83**. Tedesco was out. The agent still copied math 0.83. Tigers won 24–25. The *pick* was the favourite. The *number* ignored the prompt’s rule: name the strongest reason you could lose, and if that reason is credible, stay at or below 0.65.

### Confidence bands vs hit rate

**Modest band (about 0.55–0.65)** — 9 games, 6 correct, 3 wrong = **67%**. Roughly in line with saying “about 60%.”

Games: Storm–Sea Eagles 0.57 hit; Titans–Cowboys 0.58 hit; Warriors–Panthers 0.60 miss; Raiders–Knights 0.60 hit; Panthers–Roosters 0.60 miss; Tigers–Dragons 0.60 miss; Storm–Panthers 0.60 hit; Rabbitohs–Warriors 0.60 hit; Dragons–Bulldogs 0.65 hit.

**Clear-edge band (about 0.68–0.75)** — 13 games, 7 correct, 6 wrong = **54%**. Too many losses for numbers in this range.

Games: Dolphins–Broncos 0.74 hit; Rabbitohs–Eels 0.70 hit; Roosters–Bulldogs 0.70 hit; Dragons–Sharks 0.74 miss; Sea Eagles–Dolphins 0.68 hit; Bulldogs–Rabbitohs 0.71 miss; Sharks–Raiders 0.72 miss; Broncos–Warriors 0.72 hit; Knights–Titans 0.74 hit; Raiders–Broncos 0.72 miss; Dolphins–Eels 0.75 hit; Knights–Sea Eagles 0.70 miss; Titans–Sharks 0.73 hit.

**Rare high band (0.75–0.85):** Dolphins–Eels 0.75 hit; Roosters–Tigers 0.83 miss.

On 11 of 24 runs, agent confidence was within 0.02 of the math model’s probability for the side it picked. Mean gap between confidence and math P(picked side) was about **0.04**. Confidence is usually a near-copy of the model, then sometimes inflated by narrative (Sea Eagles vs Dolphins: math away probability 0.51, agent said 0.68 “clear edge”; Dolphins did win 0–22).

Caveat on all of these scores: **N = 24 is small**. Round 24 was upset-heavy (Roosters over Panthers, Rabbitohs over Bulldogs, Raiders over Sharks, Dragons over Tigers). Accuracy will move. The **process** patterns below (research gate, verifier, confidence-copying, Late Mail contamination) showed up in all three rounds.

---

## 1. Scene tool — working, and useful

`set_fixture_scene` ran first on every game, as designed.

**24/24** resolved the right fixture: home, away, season 2026, round, venue, kickoff. No scene errors. Cache miss on all 24 (`cache_hit=False`). Venue, kickoff, and weather were copied into `predict_match` every time. That is the rule that stops the LLM inventing a stadium.

Standings were present on all 24 (`standings.available=True`), with home and away blocks plus a comparison.

### Weather

Provider: Open-Meteo. Labels used: **Fine** (20 games) / **Rain** (4 games). No weather errors. The judge never used weather as a key factor (good — the prompt forbids it unless weather shows up in SHAP, which it did not).

Three labels look aggressive compared with the NRL ground listing:

| Game | Agent weather label | Precip (mm) | NRL field | Note |
|---|---|---|---|---|
| R23 Dragons v Sharks | Rain | 0.1 | Fine | Label aggressive |
| R23 Raiders v Knights | Rain | 0.6 | Fine | Borderline |
| R23 Storm v Sea Eagles | Rain | 1.5 | Showers | Sensible |
| R25 Titans v Sharks | Rain | 0.2 | Fine | Label aggressive |

### Standings drift mid-round

`as_at_round` is the **current** round every time, so the ladder is still moving while Friday–Sunday games are being run. Inside one ledger the home/away pair looks coherent. Across the round, the same ladder position can be claimed by different clubs:

| Round | Duplicate position | Teams |
|---|---|---|
| 23 | 9 | Bulldogs 26 pts / 19 games, Cowboys 26 / 20 |
| 23 | 12 | Storm 20/20, Raiders 22/20 |
| 24 | 5 | Sharks 32/20, Dolphins 32/20 |
| 24 | 7 | Rabbitohs 28/20, Knights 30/21 |
| 25 | 3 | Roosters 38/21, Warriors 36/21 |
| 25 | 16 | Titans 18/21, Broncos 18/21 |

### Officials

Officials were present on all 24, never an empty list. Crews are often incomplete (missing a second touch judge is common). Counts: 2 officials on 7 games, 3 on 13 games, 4 on 4 games.

**Storm vs Sea Eagles Round 23** had no Referee listed — only Touch Judge and SRO.

### Timing / too close to kickoff

`hours_before_kickoff` in the CSV is measured at **run finish**, not scene start.

| Flag | Game | Hours before KO | Notes |
|---|---|---|---|
| After kickoff | R23 Storm v Sea Eagles | **-0.1** | Finished 15:06 local; kickoff 15:00. Scene started ~14:55, still `match_mode=Pre`. Research kept a “Live Blog Super Saturday: Storm v Sea Eagles” title. |
| Under 1 hour | R24 Sharks v Raiders | 0.2 | Live blog + Zero Tackle “Live Scores” titles in research |
| Under 1 hour | R25 Titans v Sharks | 0.1 | — |
| Under 3 hours | R23 Dolphins v Broncos | 2.2 | “Live Scores” title kept |
| Under 3 hours | R23 Raiders v Knights | 2.9 | — |
| Under 3 hours | R24 Eels v Cowboys | 2.5 | Live blog |
| Under 3 hours | R24 Knights v Titans | 1.2 | “As it happened” title |
| Under 3 hours | R25 Roosters v Tigers | 2.0 | — |

For a strict pre-game evaluation, Storm Round 23, Sharks Round 24, and Titans Round 25 are the least clean runs.

---

## 2. Math tool — working, and the most useful signal

`predict_match` succeeded on **24/24**. No errors. Every response has a prediction, probability, home-win probability, SHAP explanations, and a fixture echo.

P(home win) ranged **0.2651 to 0.8330**. Mean 0.5809, median 0.5736. Never 0 or 1. Lowest: Dragons vs Sharks R23 (0.2651). Highest: Dolphins vs Eels R25 (0.8330).

SHAP drivers are the right kind of thing. Across all runs, the families that show up are:

| Category | Approx. hits | Assessment |
|---|---|---|
| Form / momentum stats | 89 | Relevant (run metres, errors, points, etc.) |
| Travel | 29 | Relevant |
| Elo | 23 | Core |
| Ladder points-difference per game | 23 | Core |
| Bradley-Terry | 22 | Core |
| Pythagorean form | 22 | Relevant |
| Rest | 16 | Relevant |
| Head-to-head | 11 | Relevant |
| Workload / venue home-ground advantage | few | Niche but sensible |

No nonsense features (random IDs, unrelated sports). CONFLICT notes appear often: the raw feature number, read on its own, favours the other side from the way the model netted the SHAP. That is expected, not garbage.

Example of a strong home blowout packet (Roosters vs Tigers R25): Bradley-Terry +0.249, Elo +0.245, ladder +0.164 → P(home) = 0.8306.

When math was decisive (Dolphins–Broncos, Broncos–Warriors, Titans–Sharks, Dolphins–Eels), the agent followed it and was usually right. When math was about 50/50, the agent did extra reasoning — mixed results, as in the three flips.

### The P(away≈) log line

On Roosters vs Tigers the log printed `P(home win)=0.8306 | P(away≈)=0.8306`. That is an **orchestrator label bug only**, in `agent/src/agent_app/orchestrator.py`. It logs `math.get("probability")` under the name `P(away≈)`.

What `probability` actually means in the payload:

- Home Win: `probability` equals `home_win_probability` → the log prints P(away) as if it were P(home). Misleading.
- Away Win: `probability` equals `1 − P(home)` → the log happens to look right.

The Roosters R25 **payload is correct**: `"prediction": "Home Win"`, `"probability": 0.8306`, `"home_win_probability": 0.8306`. Ledger math is fine. The log line is not.

### Coin-flip games (P(home) between 0.45 and 0.55)

Four games sat in this band. The model still emits a hard **Home Win** or **Away Win** label. Uncertainty lives in the probability and in `attribution_balance`, which often leans the opposite way from the hard label.

| Game | P(home) | Math hard label | SHAP leans | Agent pick |
|---|---|---|---|---|
| R23 Titans v Cowboys | 0.5063 | Home Win | away / net −0.3002 | Cowboys (override) |
| R23 Warriors v Panthers | 0.5301 | Home Win | away / net −0.2087 | Panthers (override) |
| R23 Raiders v Knights | 0.5491 | Home Win | away / net −0.1353 | Knights (override) |
| R24 Sea Eagles v Dolphins | 0.4886 | Away Win | away / net −0.368 | Dolphins (agree) |

Near-band: Storm vs Sea Eagles R23, P(home) = 0.5584 Home Win, but SHAP leans away (net −0.0995). Same pattern, no flip.

This is the real math-tool issue for the *agent*: a 50.6% home win is still labelled Home Win, while SHAP totals can lean away by a lot. The probability is the prior. The hard label plus SHAP totals are easy to over-read. That contradiction is what licensed the three flips.

`attribution_balance` is summed SHAP over **all** features, not just the top-five lists. The note in the payload says equal-length driver lists do not mean equal weight. The judge used that, but used it as a veto of P(home), which the prompt does not allow.

### `disagreements_with_math` field

In final JSON this is often the **string** `'null'` rather than JSON null. Some games that agreed with math still write prose about weighting or confidence. Cosmetic, but it makes the log harder to trust.

Agent agreed with math’s side on **21/24** games.

---

## 3. Research tool — working as a search engine, noisy as a briefing

Plumbing is healthy:

- 15–21 items kept every run.
- Official `nrl.com` always present.
- Club team lists and fixture previews exist in the pack.
- Drop filters do remove a lot of stale / wrong-round junk.
- Channels: `google_news_rss` **285** kept items, `nrl_news` **128**, `duckduckgo` **27**.

It is **not** a clean briefing for the game being predicted.

### Why the refine loop never ran

`research_refine_triggered` is **False on 24/24**. That is not because research was excellent. The gate in `agent/src/agent_app/research_gate.py` only asks:

1. At least 3 items with body text — always true (15–21).
2. Any official / `nrl_news` item **or** any availability keyword (injury, late mail, team list, casualty, …) anywhere — always true, because league-wide Late Mail and Casualty Ward are always in the pack.
3. Not every search channel hard-failed empty — never happened.

There is **no** check for: minimum items that mention both fixture teams, maximum share of league-wide roundups, or Late Mail that is actually about this game. The keep-filter also **boosts** `nrl_official_roundup` (+2.5) and `injury_or_team_list` (+1.5), so Round Late Mail wins ranking even when the headline is about another club.

### Recurring contamination

**1. Round Late Mail ranked #1 for the wrong game**

39 Late Mail titles across runs do not name either fixture team. Excerpt truncation makes this worse: the body often starts with another club’s injury, so the slim packet never reaches this fixture’s paragraph.

| Fixture | run_id | Title |
|---|---|---|
| R23 Dolphins v Broncos | `20260808T050615Z-aa39550b` | “NRL Late Mail: Round 23 - Rabbitohs lose Graham; Best sidelined” — score 8.0, keep reason `nrl_official_roundup` |
| R24 Eels v Cowboys | `20260815T044822Z-a99ec147` | “NRL Late Mail: Round 24 - Crossland back, Best on hold for Knights” — body opens on Knights/Titans |
| R25 Dragons v Bulldogs | `20260822T020223Z-7e51b39e` | “NRL Late Mail: Round 25 - Latrell on hold; Turbo on track” — Rabbitohs/Manly headline for a Dragons–Bulldogs packet |

Counter-example of Late Mail that *was* on-fixture: Warriors vs Panthers R23 (`20260807T011224Z-bf2eb8b8`) — Late Mail about Tedesco / Metcalf / Talagi.

**2. Permanent Casualty Ward URL, all 24 runs**

Every run keeps:

`https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/`

Titles rotate (“Panthers' Yeo blow…”, “Surgery for Doueihi, Walsh…”). `published_at` looks fresh. The **canonical URL is 2026-01-01**. League-wide injury lead is scored 5.0 via `nrl_official_roundup` whether or not it is about this fixture.

**3. Other clubs’ team lists and Late Mail kept as “round roundup”**

| Fixture | run_id | Contaminant |
|---|---|---|
| R24 Eels v Cowboys | `20260815T044822Z-a99ec147` | Sharks “NRL Late Mail: Round 24 v Raiders” (sharks.com.au) |
| R24 Eels v Cowboys | same | Wests Tigers “Team List: NRL Round 24 v Dragons” |
| R23 Rabbitohs v Eels | `20260808T051614Z-181ab3a6` | Sharks “NRL Team List: Round 23 v Dragons” |
| R25 Dragons v Bulldogs | `20260822T020223Z-7e51b39e` | Wests Tigers “Team List: NRL Round 25 v Roosters” |

Also: other-game Match Previews promoted after body fetch. Example: Dolphins vs Broncos packet includes Raiders v Knights, Storm v Sea Eagles, Bulldogs v Cowboys previews (`.../Round 23/2026-R23_Dolphins-v-Broncos/20260808T050615Z/ledger.json`).

**4. Other-fixture Before You Bet / tips pages**

About 16–18 clear other-game Before You Bet pages kept via `league_round_roundup` (round number matches, fixture teams not in the title), e.g.:

- R24 Broncos v Warriors (`20260815T051954Z-7040bd6a`): Tigers vs Dragons, Panthers vs Roosters
- R24 Eels v Cowboys (`20260815T044822Z-a99ec147`): Broncos vs Warriors, Knights vs Titans
- R25 Dragons v Bulldogs (`20260822T020223Z-7e51b39e`): Rabbitohs vs Warriors, Knights vs Sea Eagles, Raiders vs Broncos

These often carry **wrong-game dollar prices** into `market_mentions` / body. Example: R24 Sharks vs Raiders keeps Bulldogs–Rabbitohs tips with `$1.83`.

**5. NSW Cup and similar**

R25 Dragons vs Bulldogs: an NSW Cup team list can outrank the NRL preview (item #3).

### Per-round snapshots

**Round 23.** Universal Late Mail / Casualty Ward contamination. Dolphins–Broncos: 5+ wrong-game NRL previews plus Fox Late Mail about Knights/Souths kept with `mentions_both_teams` (body name-drops). Warriors–Panthers Late Mail was better than average for this failure mode.

**Round 24.** Heaviest other-game Before You Bet and club Late Mail bleed (Sharks v Raiders Late Mail into Eels–Cowboys and Knights–Titans). Eels–Cowboys top item is Knights Late Mail; also Tigers team list, Sharks Late Mail, Broncos/Knights Before You Bet, News.com.au Raiders axe story. Knights–Titans: Cowboys team list (Eels), Sharks Late Mail, Tigers Before You Bet, Sharks–Raiders replay.

**Round 25.** Same Late Mail / Casualty pattern. Dragons–Bulldogs: 5 neither-team / multi-other items; Late Mail about Latrell/Turbo; three other-game Before You Bet pages. Storm–Panthers was cleaner on titles, still keeps league Late Mail / Casualty Ward.

### Is research actually useful for injuries and form?

Yes, **when the judge finds the right subset**. Final `key_factors` with `source: "research"` are mostly on-fixture:

| Quality | Examples (run_id) |
|---|---|
| Strong availability | Reynolds concussion + Duffy — Dolphins–Broncos `aa39550b` (broncos.com.au team list). Nanai out / Ilias return — Titans–Cowboys `77e7df21`. Tedesco / Yeo — Panthers–Roosters `c5568e72`. Best + Saifiti back / Walsh jaw — Knights–Sea Eagles `e7b3d151`. Fonua-Blake return — Titans–Sharks `9d999b11`. |
| Strong form / stakes | Sharks 10/11 — Dragons–Sharks `f94e3aa5`. Finals pressure on Bulldogs — Dragons–Bulldogs `7e51b39e`. Titans conceded 108 points in three games — Titans–Sharks. |
| Weaker / secondary | Head-to-head narrative from Before You Bet (Eels–Cowboys). Form blurbs from sportsnews without tying to lists. |

Useful signal exists in the **middle of the pack** (club team lists, fixture match previews). **Noise dominates rank 1–2** and wastes context window. Judges usually ignore the worst contaminants for the final key factors. Thinking traces still chew through wrong Late Mail and market prices.

Wrong-article risk examples:

- Storm vs Panthers cites “NRL Late Mail: Round 25” for Harry Grant. That article may mention Grant, but the shared Late Mail is not fixture-scoped. Safer cite: the dedicated Match Preview Storm v Panthers.
- Roosters vs Bulldogs Late Mail body opening discusses Warriors/Panthers while the fixture is Roosters–Bulldogs (`dc44cdf6` thinking path).

### Odds / prices — not mostly hallucination

Sportsnews tips pages put `$x.xx` deep in the article. Example: Dragons–Sharks `$1.20` at character 1436, body length 2398. Judgement slims research to **top 12 items × `body_excerpt[:800]`**, so prices vanish from the research items the verifier sees. Meanwhile `extract_market_mentions()` scans the **full** body and puts `$1.20` in `prices_found`.

What happens in practice:

| Layer | What happens |
|---|---|
| Full `body_excerpt` | Fixture tips pages usually contain `$x.xx` (often past character 800) |
| `market_mentions.prices_found` | Extracted from full body; judge sees them |
| Slim research for LLM / verifier | Top 12 × 800 chars → prices often absent |
| Thinking | Frequently quotes those prices (22/24 runs) |
| Verifier | Fails `sourced_claims` on price in **11/24** last audits |
| Final judgement | Usually strips `$`. Only **1/24** finals still contain `$x.xx`: Warriors–Panthers `$1.60` |

So the 11 `sourced_claims` fails are mostly a **grounding path mismatch** (full-body market extract vs slim body check), not invented numbers. Contaminated prices from other-game Ladbrokes / Before You Bet pages remain a real risk when those items stay in the pack. Ladbrokes round wraps also inject unrelated pairs like `$1.90` / `$16.31`.

### Channel mix

| Channel | Role in practice |
|---|---|
| `nrl_news` | Official, but the filter treats round Late Mail / Casualty / Team Lists as high-value → contamination amplifier |
| `google_news_rss` | Majority of items. Best club lists **and** other-game Before You Bet / sportingnews |
| `duckduckgo` | Sparse. Often club Late Mail for the **wrong** opponent (Sharks v Raiders into unrelated runs) |

Official sources (nrl.com + club `.com.au`) are present in every run. Presence alone satisfies the gate. It does not mean the content is about this fixture.

Typical drop stats from a summary (Titans–Cowboys R23): kept 18; dropped stale 51, wrong_round 7, noise 15, irrelevant 14, duplicate_url 3, no_body 4. The filter is doing real work. What it keeps is still noisy.

---

## 4. Query planner — working, and a bit mechanical

Every run produces the same five shapes:

1. Home availability (`<team> NRL injury OR "late mail" OR "team list" round N`)
2. Away availability (same shape)
3. Fixture preview (`<home> vs <away> NRL round N preview`)
4. Odds (`<home> <away> NRL odds OR price OR favourite`)
5. Finals / form / ladder stakes

Those merge with the tool’s default templates (DD-29), so the CSV shows about **10 queries** per run. That is doing what it was designed to do: a weak LLM plan cannot drop injury coverage.

The planner almost never writes a *fixture-specific* fifth query (a named returning player, a coach-pressure angle). It defaults to “finals race / ladder stakes.” Fine, not insightful. It correctly avoids weather, venue, and referee searches. Team nicknames match the scene (including `Wests Tigers`).

Thinking traces for query plan show the model walking the prompt checklist (keywords only, no questions, order of importance). It is following instructions, not exploring.

---

## 5. Judge reasoning — usually sound, not faithful to the prompt on the hard ones

The judge is the only component allowed to pick a winner. Tools return facts only. That architecture is being respected.

### What it does well

- Invents almost no injuries or ladder positions.
- Availability **direction** is generally right (returning vs out). Nanai out / Ilias return; Best out (R23) then back (R25); Grant returning; Tedesco / Yeo out; Fonua-Blake back. No clear inverted injury in the high-risk set.
- Does not use weather as a key factor (24/24 `weather_not_headline` pass).
- On blowouts it follows Elo / Bradley-Terry / ladder and cites a real research item.
- Sometimes *does* discount math with team news the way the prompt wants: Panthers vs Roosters dropped confidence 0.66 → **0.60** for Yeo / Tedesco (still lost; Roosters 6–12).
- Thinking traces show actual weighing, not a one-line copy of the model.

### Where it goes wrong

**1. `attribution_balance` as a veto of P(home).**

The prompt says the model probability is the prior. Research adjusts it; research does not replace it. On the three flips the judge treated SHAP totals as more real than ~0.53.

Quotes from thinking / summary:

Titans vs Cowboys (`thinking.md`):

> I will lean toward the Cowboys because of the Elo and Bradley-Terry strength... The 'Home Win' prediction by the math model is so slim that it doesn't override the structural advantage

Warriors vs Panthers (`summary.md`):

> The model probability predicts a Home Win (0.53), but I am picking Away because the attribution_balance leans strongly toward Penrith (0.59 vs 0.38) and they are the market favorites ($1.60).

Raiders vs Knights (`thinking.md`) — the clearest prompt violation:

> The qualitative evidence (standings, recent form) strongly favours the Knights.
>
> I am picking Away because the official standings and recent form strongly outweigh the latent strength indicators (Elo/Bradley-Terry)

On Raiders vs Knights the thinking also noted Bradman Best was sidelined (a reason *against* Knights) and still flipped to Knights @ 0.60. Knights did win 24–30. The result does not make the reasoning match the prompt.

**2. Market and head-to-head overweight.**

Warriors vs Panthers: Panthers because they are `$1.60` favourites.

Eels vs Cowboys (`thinking.md`):

> The historical dominance of the Eels over the Cowboys (5 of 6 wins) and the specific struggle for North Queensland at CommBank Stadium are significant qualitative factors

Happened to be right. Still the wrong kind of reason relative to the design. SHAP did include head-to-head (80% home win last 5) as a driver favouring Eels; Elo and Bradley-Terry were pulling for Cowboys; `attribution_balance` leaned away. The judge chose H2H/venue over ratings.

**3. Confidence is not an independent number.**

Design (ADR 0009): the judge’s confidence is its own number, not a copy of the model, so the agent’s Brier score can be compared with the model’s.

Observed:

- Near-copy (`|gap| < 0.02`): **11/24**
- Mean `|gap|`: **0.041**
- Large inflation on flips / narrative: Raiders–Knights +0.15 (0.60 vs math P(away) ≈ 0.45), Warriors–Panthers +0.13, Titans–Cowboys +0.09, Sea Eagles–Dolphins +0.17

Sea Eagles vs Dolphins (`summary.md`): math P(home) = 0.4886 so math P(Dolphins) ≈ 0.51. Agent confidence **0.68**:

> Confidence: 0.68 (Clear edge due to form disparity and ratings...

Dolphins won 0–22. The pick was right. The number is narrative inflation, not calibration.

Roosters vs Tigers: prompt band 0.75–0.85 is “rare: a large ratings gap confirmed by team news.” Team news was Tedesco **out** (Ramsey at fullback). Confidence stayed **0.83**, matching math. Tigers won 24–25.

Knights vs Sea Eagles: kept **0.70** while noting Turbo was back and Walsh was out. Sea Eagles won 24–44.

**4. High band is misused.**

0.70+ hit rate 54%, as scored above. The prompt says most fixtures belong in 0.55–0.65. These runs put 13 of 24 in the “clear edge” band or above.

### Prompt checklist vs observed

| Expectation | Observed |
|---|---|
| Math as prior | Usually yes on agree-with-math games. Broken on the 3 flips via `attribution_balance` override |
| Research adjusts | Often used correctly (named injuries, form notes) |
| Don’t invent facts | Dollar odds frequently unsourced in the slim packet (11/24) |
| Weigh SHAP by contribution | Usually cites Elo / Bradley-Terry. Sometimes elevates H2H (Eels) |
| CONFLICT drivers | Usually acknowledged when recalibrating. Sometimes ignored on the first pass |
| Weather not a headline | Pass on all 24 |

### High-risk games, short notes

| Game | What happened |
|---|---|
| Titans–Cowboys R23 | Flip. Justified only if `attribution_balance` is treated as co-equal with the probability. Cowboys won 8–30. |
| Warriors–Panthers R23 | Flip. Market / ladder overweight. Warriors won 28–12. |
| Raiders–Knights R23 | Flip. Clearest prompt violation (standings/form over Elo/BT). Knights won 24–30. |
| Eels–Cowboys R24 | Agreed Eels. Narrative tempted Cowboys. H2H-heavy. Eels won 32–30. |
| Panthers–Roosters R24 | Agreed Panthers. Lowered conf 0.66→0.60 for Yeo (good research adjust). Roosters won 6–12. |
| Sea Eagles–Dolphins R24 | Agreed Dolphins. Conf inflated 0.51→0.68. Dolphins won 0–22. |
| Storm–Panthers R25 | Agreed Panthers. Grant return correctly directional. Panthers won 14–22. |
| Titans–Sharks R25 | Agreed Sharks. Clean reasoning. Sharks won 22–30. |
| Knights–Sea Eagles R25 | Agreed Knights @ 0.70. Noted Turbo back and Walsh out, did not lower enough. Sea Eagles won 24–44. |
| Roosters–Tigers R25 | Agreed Roosters 0.83 ≈ math 0.83. Tedesco out not used to cut confidence. Tigers won 24–25. |

---

## 6. Verifier — working as a linter, not as a check on reasoning

Two stages: a coded checklist, then an LLM audit. If the audit fails, the judge recalibrates **once**, same session, no new tools.

| Metric | Count |
|---|---|
| Canonical runs | 24 |
| Checklist pass | **24/24** |
| Audit pass | **1/24** (only Roosters v Bulldogs R23) |
| Recalibration triggered | **23/24** |
| Winner changed after recalibration | **0/23** |
| Confidence changed after recalibration | **0/23** |
| Fail: `omitted_math_signals` | **23** |
| Fail: `sourced_claims` (market `$`) | **11** |

The coded checklist only asks structural things: all three tools ran, confidence is between 0.50 and 0.95, at least one key factor is sourced from research if research returned items. It always passes. Weather is deliberately **not** in the checklist (a keyword scan once treated “hamstring strain” as weather because `rain` sits inside `strain`).

The LLM audit is designed to fail if the top SHAP names on **both** lists are not mentioned. Driver lists are padded to five, including tiny / CONFLICT rows. So the judge is almost always told to “consider Bradley-Terry / travel / kicking metres.” Typical instruction:

> Math drivers include 'Home travel to venue (0 km)' and 'Bradley-Terry strength advantage'; they are not addressed in your evaluation — please consider them and re-output.

The judge then pastes those names into the summary and keeps the **same pick** and the **same confidence**. Example Titans–Cowboys: summary grew from 331 to 524 characters; still Cowboys @ 0.58.

That is **documentation hygiene**, not quality control. It does usefully strip some unsourced `$` prices from the final JSON. It has never, in these 24 games, caught a bad flip or an overconfident 0.83.

`weather_not_headline`, `availability_direction`, `research_used`, `driver_proportionality` generally pass. `confidence_justified` also generally passes even when the number is a copy of math P — because the audit is told **not** to compare confidence with the model probability.

Pattern: **audit fail → recalibrate → identical pick**. 23 times.

---

## What this means for “are the tools useful?”

| Tool | Working? | Useful for *this* game? |
|---|---|---|
| Scene | Yes | Yes — identity, kickoff, ladder. Weather and officials are secondary. |
| Math | Yes | **Yes, the main signal.** Weakest when it emits Home Win at ~51% plus a contradictory SHAP balance. |
| Research | Yes | **Partly.** Club lists and named injuries are useful. The ranked pack is a round-wide scrapbook. The gate cannot tell those apart. |
| Query planner | Yes | Adequate coverage. Little fixture-specific curiosity. |
| Judge | Yes | Good synthesizer of a clean packet. Unreliable editor of a messy one. Overconfident. |
| Verifier | Yes | Almost never changes the decision. |

The failure mode is not “the LLM ignores the tools.” It is: the tools dump more than one game’s worth of news; math presents a coin-flip as a Home Win; and the judge + verifier spend their extra step renaming SHAP drivers.

---

## Ranked findings (severity for the capstone)

1. **Calibration, not picking, is the weak result.** 62.5% sides vs a 0.256 Brier that loses to P=0.5. The 0.70+ band hit 54%. That undercuts ADR 0009’s claim that agent confidence is a meaningful independent probability.

2. **Research quality is not the same as research volume.** Refine-never-firing is a false all-clear. Fixture-specific Late Mail and team lists exist but do not dominate the packet.

3. **Verifier loop is ceremonial** on winner and confidence. `omitted_math_signals` as currently written guarantees churn.

4. **Coin-flip math UX drives the only extra “agency” the judge shows.** Two of those three calls were correct after the fact. The mechanism is still “trust SHAP totals over P(home),” which the prompt forbids.

5. **Odds grounding is a packet bug**, not mostly hallucination. Verifier and judge look at different slices of the same article.

6. **Three runs are tainted for strict pre-game evaluation** (Storm after kickoff; Sharks R24 and Titans R25 inside an hour), with live-blog titles in the research pack.

7. **Scene/math wiring and availability direction are genuine strengths** and show up in the artefacts.

---

## Canonical run index

All under `agent_runs/fixtures/`.

| Round | Fixture folder | run_id |
|---|---|---|
| 23 | `Round 23/2026-R23_Titans-v-Cowboys/20260806T052234Z` | `20260806T052234Z-77e7df21` |
| 23 | `Round 23/2026-R23_Warriors-v-Panthers/20260807T011224Z` | `20260807T011224Z-bf2eb8b8` |
| 23 | `Round 23/2026-R23_Roosters-v-Bulldogs/20260807T012943Z` | `20260807T012943Z-dc44cdf6` |
| 23 | `Round 23/2026-R23_Storm-v-Sea-Eagles/20260808T045530Z` | `20260808T045530Z-134a1247` |
| 23 | `Round 23/2026-R23_Dolphins-v-Broncos/20260808T050615Z` | `20260808T050615Z-aa39550b` |
| 23 | `Round 23/2026-R23_Rabbitohs-v-Eels/20260808T051614Z` | `20260808T051614Z-181ab3a6` |
| 23 | `Round 23/2026-R23_Raiders-v-Knights/20260809T005509Z` | `20260809T005509Z-be2ac1aa` |
| 23 | `Round 23/2026-R23_Dragons-v-Sharks/20260809T010720Z` | `20260809T010720Z-f94e3aa5` |
| 24 | `Round 24/2026-R24_Panthers-v-Roosters/20260813T044820Z` | `20260813T044820Z-c5568e72` |
| 24 | `Round 24/2026-R24_Sea-Eagles-v-Dolphins/20260814T012715Z` | `20260814T012715Z-b5649b42` |
| 24 | `Round 24/2026-R24_Bulldogs-v-Rabbitohs/20260814T013835Z` | `20260814T013835Z-4368793d` |
| 24 | `Round 24/2026-R24_Sharks-v-Raiders/20260815T043801Z` | `20260815T043801Z-73529dbb` |
| 24 | `Round 24/2026-R24_Eels-v-Cowboys/20260815T044822Z` | `20260815T044822Z-a99ec147` |
| 24 | `Round 24/2026-R24_Broncos-v-Warriors/20260815T051954Z` | `20260815T051954Z-7040bd6a` |
| 24 | `Round 24/2026-R24_Knights-v-Titans/20260816T023648Z` | `20260816T023648Z-7caa309d` |
| 24 | `Round 24/2026-R24_Wests-Tigers-v-Dragons/20260816T024747Z` | `20260816T024747Z-5d316970` |
| 25 | `Round 25/2026-R25_Storm-v-Panthers/20260820T033325Z` | `20260820T033325Z-7e761a86` |
| 25 | `Round 25/2026-R25_Raiders-v-Broncos/20260821T020057Z` | `20260821T020057Z-55e11046` |
| 25 | `Round 25/2026-R25_Dolphins-v-Eels/20260821T021346Z` | `20260821T021346Z-e66f4459` |
| 25 | `Round 25/2026-R25_Knights-v-Sea-Eagles/20260822T011159Z` | `20260822T011159Z-e7b3d151` |
| 25 | `Round 25/2026-R25_Rabbitohs-v-Warriors/20260822T013308Z` | `20260822T013308Z-486b4dcd` |
| 25 | `Round 25/2026-R25_Dragons-v-Bulldogs/20260822T020223Z` | `20260822T020223Z-7e51b39e` |
| 25 | `Round 25/2026-R25_Titans-v-Sharks/20260823T034140Z` | `20260823T034140Z-9d999b11` |
| 25 | `Round 25/2026-R25_Roosters-v-Wests-Tigers/20260823T035224Z` | `20260823T035224Z-1558e4fa` |

Each run folder contains `ledger.json`, `summary.md`, `thinking.md`, `record.json`. Aggregate log: `agent_runs/predictions_log.csv`.

---

## ETL note (for context, not part of the 24-run process audit)

Weekly ETL on 24 August 2026 retrained successfully after Round 25 completed:

- Before: `trained_at=2026-08-18T02:45:04Z`, 2382 rows, 180 raw 2026 files
- After: `trained_at=2026-08-24T08:01:53Z`, 2390 rows, 188 raw 2026 files
- 8/8 Round 25 matches scraped, 0 failures
- The 24 predictions above were made **before** this retrain (model at the time: 18 August, 2382 rows)

---

## Bottom line

The system runs end to end. Scene and math are trustworthy. Research returns enough real injury and team-list facts that the judge can usually cite them, but it also returns a lot of other games’ news, and nothing in the gate complains. The judge is a competent reader of a clean packet and an overconfident reader of a messy one. The verifier asks it to name leftover SHAP rows and then accepts the same pick.

If you only remember four numbers: **15/24 sides correct**, **Brier 0.256 (worse than 50/50)**, **0/23 verifier pick changes**, **0/24 research refine loops**.
