# Roosters v Wests Tigers

- **Run**: `20260823T035224Z-1558e4fa`
- **When**: 2026-08-23T03:52:24.508574+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-23T16:05:00+10:00 at Allianz Stadium (round 25)

## Verdict

**Roosters** to win, confidence 83%.

> The Roosters are dominant, sitting 3rd on the ladder with a five-game winning streak, while the Wests Tigers are 15th and have lost four straight. While the math model notes some minor drivers favoring the Tigers in 5-game points and 3-game kicking metres, these are low-weight signals (combined 5%) and are explicitly marked as conflicted, meaning the raw values actually favor the Roosters. With a massive Elo advantage and a 22.5-point market spread, the Roosters remain heavy favorites despite the absence of James Tedesco.

### Key factors

- **math** — Strong Bradley-Terry and Elo rating advantages (combined contribution ~0.49), far outweighing the negligible and conflicted drivers favoring the Tigers.
- **scene** — Stark contrast in standings and form: Roosters are 3rd (16-5) on a 5-game win streak, while Wests Tigers are 15th (7-14) on a 4-game losing streak.
- **research** — James Tedesco is ruled out of the match due to an ankle injury, with Cody Ramsey starting at fullback (nrl_news).

## What the maths said

- Prediction: **Home Win**
- P(Roosters win) = **0.8306**

| Favouring Roosters (home) | Favouring Wests Tigers (away) |
| --- | --- |
| Bradley-Terry strength advantage (+1.62 log-strength) — contribution 0.249 (16% of total) | 5-game form: points for (+20.00) — contribution 0.043 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Elo rating advantage (+301 points) — contribution 0.245 (16% of total) | 3-game form: kicking metres (+100.67) — contribution 0.033 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Ladder points differential per game (+17.9 points) — contribution 0.164 (10% of total) | Travel-distance advantage (+7 km for away) — contribution 0.031 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| 5-game form: all run metres (+205.00) — contribution 0.152 (10% of total) | 5-game form: possession pct (+2.80) — contribution 0.020 (1% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Pythagorean form (last 10) (+72% expected-win gap) — contribution 0.122 (8% of total) | 5-game form: post contact metres (+84.20) — contribution 0.018 (1% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |

- Attribution balance: leans **home** (home 1.392, away 0.1862)
- Value/contribution conflicts:
  - 5-game form: points for (+20.00)
  - 3-game form: kicking metres (+100.67)
  - Travel-distance advantage (+7 km for away)
  - 5-game form: possession pct (+2.80)
  - 5-game form: post contact metres (+84.20)

## Ladder standings

As at round 25 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=25)).

- **Roosters** — 3th · 16-0-5 · PD +163 (+7.76/g)
- **Wests Tigers** — 15th · 7-0-14 · PD -213 (-10.14/g)

- Higher on ladder: **Roosters**
- Points-difference favours: **Roosters** (home−away PD/game gap: 17.9)

## What the research found

21 items kept (dropped: stale 46, wrong_round 4, noise 12, irrelevant 14, duplicate_url 2, no_body 2).

- [NRL Late Mail: Round 25 - Teddy out again](https://www.nrl.com/news/2026/08/19/nrl-late-mail-round-25---trell-touch-and-go-best-good-to-go/)  
  `nrl_news` 2026-08-23T02:35:27+00:00
- [NRL Team Lists: Round 25](https://www.nrl.com/news/2026/08/18/nrl-team-lists-round-25/)  
  `nrl_news` 2026-08-18T06:00:29+00:00
- [Team List: NRL Round 25 v Roosters - Wests Tigers](https://www.weststigers.com.au/news/2026/08/18/team-list-nrl-round-25-v-roosters2/)  
  `google_news_rss` 2026-08-18T06:00:00+00:00
- [Sydney Roosters vs Wests Tigers Tips, Odds, Teams & Predictions – NRL Round 25 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/sydney-roosters-vs-wests-tigers-tips-odds-teams-predictions-nrl-round-25-2026/609976/amp)  
  `google_news_rss` 2026-08-20T03:14:02+00:00
- [NRL Sunday: Titans v Sharks; Roosters v Wests Tigers Presented by 30 mins ago](https://www.nrl.com/news/2026/08/23/nrl-sunday-titans-v-sharks-roosters-v-wests-tigers/)  
  `nrl_news` 2026-08-23T03:22:49+00:00
- [NRL Casualty Ward: Koula injures ankle; Tedesco still hobbled](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-08-22T12:54:28+00:00
- [Roosters vs Tigers Preview & Betting Tips: NRL Round 25 2026 - Before You Bet](https://www.beforeyoubet.com.au/roosters-vs-tigers-preview-betting-tips-nrl-round-25-2026)  
  `google_news_rss` 2026-08-22T07:58:13+00:00
- [Match Preview Roosters v Wests Tigers: Teddy still out; Madden steps up](https://www.nrl.com/news/2026/08/18/roosters-v-wests-tigers-teddy-returns-doueihi-set-for-surgery/)  
  `nrl_news` 2026-08-22T06:12:48+00:00
- [24 Hour Update | Round 25 v Tigers - Sydney Roosters](https://www.roosters.com.au/news/2026/08/22/nrl-teamlist--round-25-v-tigers/)  
  `google_news_rss` 2026-08-22T05:58:00+00:00
- [NRL Coach Media | Round 25 v Tigers - Sydney Roosters](https://www.roosters.com.au/news/2026/08/22/nrl-coach-media--round-25-v-tigers/)  
  `google_news_rss` 2026-08-22T02:17:20+00:00
- [Roosters v Wests Tigers: Round 25 - NRL.com](https://www.nrl.com/news/2026/08/19/roosters-v-wests-tigers-round-25/)  
  `google_news_rss` 2026-08-19T05:43:17+00:00
- [Jersey Flegg Cup: Round 25 - Wests Tigers](https://www.weststigers.com.au/news/2026/08/18/wests-tigers---jersey-flegg-cup-round-25/)  
  `google_news_rss` 2026-08-18T06:07:00+00:00
- [Roosters vs Wests Tigers - Round 25, 2026 - Live Scores & Stats - Match Centre - Zero Tackle](https://www.zerotackle.com/roosters-wests-tigers-round-25-2026-mc10396531-237057/)  
  `google_news_rss` 2026-08-16T21:10:45+00:00
- [NRL Round 25 team lists: Full squads + NRL Supercoach analysis - SC Playbook NRL](https://scplaybook.com.au/blog/2026/08/18/nrl-round-25-team-lists-full-squads-nrl-supercoach-analysis)  
  `google_news_rss` 2026-08-18T06:26:31+00:00
- [NRL Team List: Round 25 vs. Bulldogs - St George Illawarra Dragons](https://www.dragons.com.au/news/2026/08/18/nrl-team-list-round-25-vs.-bulldogs/)  
  `google_news_rss` 2026-08-18T05:57:35+00:00
- [NRL Late Mail: Round 25 v Titans](https://www.sharks.com.au/news/2026/08/23/nrl-late-mail-round-25-v-titans/)  
  `duckduckgo` 2026-08-18T03:53:16+00:00
- [Wests Tigers NRL Injury Report Round 25 - Wests Tigers](https://www.weststigers.com.au/news/2026/08/18/wests-tigers-nrl-injury-report-round-25/)  
  `google_news_rss` 2026-08-18T03:14:30+00:00
- [NRL Final Team: Round 25 vs. Bulldogs - St George Illawarra Dragons](https://www.dragons.com.au/news/2026/08/22/nrl-team-update-round-25-vs2.-bulldogs/)  
  `google_news_rss` 2026-08-22T08:05:00+00:00
- [NRL 2026: Confirmed lineups, results for Round 25 - sportingnews.com](https://www.sportingnews.com/au/rugby-league/news/nrl-team-lists-round-25-2026-lineups-injuries-results/6d589fc01ec29d216192b2fb)  
  `google_news_rss` 2026-08-21T10:18:00+00:00
- [NRL Team Update: Round 25 vs. Bulldogs - St George Illawarra Dragons](https://www.dragons.com.au/news/2026/08/21/nrl-team-update-round-25-vs.-bulldogs/)  
  `google_news_rss` 2026-08-21T09:32:00+00:00
- [2026 NRL Round 25 Predictions - Ladbrokes](https://www.ladbrokes.com.au/blog/2026/08/19/2026-nrl-round-25-predictions/)  
  `google_news_rss` 2026-08-19T05:28:23+00:00

## Queries the agent wrote

- `Roosters NRL injury OR "late mail" OR "team list" round 25`
- `Wests Tigers NRL injury OR "late mail" OR "team list" round 25`
- `Roosters vs Wests Tigers NRL round 25 preview`
- `Roosters Wests Tigers NRL odds OR price OR favourite`
- `Roosters Wests Tigers NRL form OR finals race`
- `Roosters Wests Tigers NRL`
- `Roosters NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Wests Tigers NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Roosters Wests Tigers NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 25 Roosters OR Wests Tigers`

## Loops

- **Research refine**: not needed (gate passed: True, 21 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The judgement fails to evaluate the top math signals favouring the Wests Tigers.
    - recalibrated: home 0.83 → home 0.83

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | Tedesco's absence is in nrl_news, Ramsey's start is in google_news_rss, and the 22.5-point spread is in google_news_rss. |
| `availability_direction` | pass | Judgement correctly describes Tedesco as missing, matching the source 'will miss a third straight game'. |
| `shap_attribution` | pass | Bradley-Terry, Elo, and points differential are correctly attributed to the Roosters' advantage. |
| `weather_not_headline` | pass | Weather is not mentioned as a key factor. |
| `research_used` | pass | Key factor 3 is sourced from research and cites nrl_news. |
| `confidence_justified` | pass | Confidence of 0.83 is within the 0.50-0.85 range and justified by the statistical gap. |
| `driver_proportionality` | pass | The judgement relies on the dominant SHAP drivers (BT strength, Elo) rather than minor ones. |
| `omitted_math_signals` | fail | Top drivers for Wests Tigers ('5-game form: points for' and '3-game form: kicking metres') are not mentioned or alluded to. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.