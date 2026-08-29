# Roosters v Dolphins

- **Run**: `20260829T043205Z-57ceff60`
- **When**: 2026-08-29T04:32:05.300431+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-29T17:30:00+10:00 at Allianz Stadium (round 26)

## Verdict

**Roosters** to win, confidence 60%.

> The Roosters are favoured by the math model and bookmakers, with the return of James Tedesco from an ankle injury providing a key boost (NRL news). While the Dolphins carry strong form with a four-game winning streak, the Roosters maintain a strength advantage and home-ground edge. Confidence is set at 0.60, aligning with the math prior and the positive news of Tedesco's return, while accounting for the Dolphins' current momentum.

- **Research vs math:** confirms
- **Strongest reason it could lose:** The Dolphins enter the match with significant momentum on a four-game winning streak, while the Roosters are coming off a shock loss to the Tigers.
- **Loss reason is specific:** True

### Key factors

- **math** — Bradley-Terry strength advantage provided the largest contribution to the model's prior (18% of total SHAP mass).
- **research** — Skipper James Tedesco is set to make his comeback from an ankle injury (NRL news).
- **scene** — The Roosters hold a slight edge on the official ladder, sitting 3rd compared to the Dolphins in 4th.

## What the maths said

- Prediction: **Home Win**
- P(Roosters win) = **0.6030**

| Favouring Roosters (home) | Favouring Dolphins (away) |
| --- | --- |
| Bradley-Terry strength advantage (+0.30 log-strength) — contribution 0.152 (18% of total) | 5-game form: all run metres (-186.80) — contribution 0.083 (10% of total) |
| Ladder points differential per game (+1.1 points) — contribution 0.058 (7% of total) | 3-game form: errors (-2.00) — contribution 0.029 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Head-to-head average margin (last 5) (+9.2 points) — contribution 0.046 (5% of total) | 3-game form: all run metres (-243.67) — contribution 0.024 (3% of total) |
| Elo rating advantage (+26 points) — contribution 0.040 (5% of total) | 5-game form: missed tackles (+3.00) — contribution 0.024 (3% of total) |
| Head-to-head record (last 5) (80% to the home side) — contribution 0.036 (4% of total) | 3-game form: kicking metres (+172.00) — contribution 0.023 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |

- Attribution balance: leans **home** (home 0.464, away 0.3768)
- Value/contribution conflicts:
  - 3-game form: errors (-2.00)
  - 3-game form: kicking metres (+172.00)

## Ladder standings

As at round 26 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=26)).

- **Roosters** — 3th · 16-0-6 · PD +162 (+7.36/g)
- **Dolphins** — 4th · 15-0-7 · PD +138 (+6.27/g)

- Higher on ladder: **Roosters**
- Points-difference favours: **Roosters** (home−away PD/game gap: 1.09)

## What the research found

17 items kept (dropped: stale 49, wrong_round 4, noise 13, irrelevant 20, roundup_no_fixture_team 6, evergreen_casualty_ward 1, duplicate_url 3, no_body 5).

- [Team Lists NRL Late Mail: Round 26 - Cleary set to debut Presented by 23 mins ago](https://www.nrl.com/news/2026/08/26/nrl-late-mail-round-26/)  
  `nrl_news` 2026-08-29T04:09:09+00:00
- [Roosters vs Dolphins Preview (Round 26, 2026): Team News, Team Lists & Prediction](https://rugbyleaguezone.com/roosters-vs-dolphins-round-26-preview-2026-437475/)  
  `duckduckgo` 2026-08-28T04:32:48+00:00
- [Dolphins Team List: Round 26 v Roosters - Official website of The Dolphins](https://www.dolphinsnrl.com.au/news/2026/08/25/dolphins-team-list-round-26-v-roosters/)  
  `google_news_rss` 2026-08-25T05:59:51+00:00
- [Match Preview Roosters v Dolphins: Teddy set to play; Donoghoe good to go](https://www.nrl.com/news/2026/08/25/roosters-v-dolphins-teddy-set-to-play-donoghoe-eyes-return/)  
  `nrl_news` 2026-08-28T07:34:27+00:00
- [Sydney Roosters vs Dolphins Tips, Odds, Teams & Predictions – NRL Round 26 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/sydney-roosters-vs-dolphins-tips-odds-teams-predictions-nrl-round-26-2026/610056)  
  `google_news_rss` 2026-08-27T02:21:44+00:00
- [Sydney Roosters vs Dolphins Tips, Odds, Teams & Predictions – NRL Round 26 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/sydney-roosters-vs-dolphins-tips-odds-teams-predictions-nrl-round-26-2026/610056/amp)  
  `google_news_rss` 2026-08-26T23:17:35+00:00
- [2026 NRL Round 26 Predictions - Ladbrokes](https://www.ladbrokes.com.au/blog/2026/08/27/2026-nrl-round-26-predictions/)  
  `google_news_rss` 2026-08-26T22:07:42+00:00
- [Dolphins Life of Brian: Dolphins rookie Pouniu ready to ride the wave](https://www.nrl.com/news/2026/08/25/life-of-brian-dolphins-rookie-pouniu-ready-to-ride-the-wave/)  
  `nrl_news` 2026-08-24T23:54:04+00:00
- [Match Preview: Round 26 – Dolphins v Roosters - Official website of The Dolphins](https://www.dolphinsnrl.com.au/news/2026/08/29/match-preview-round-26--dolphins-v-roosters/)  
  `google_news_rss` 2026-08-28T23:45:23+00:00
- [Dolphins Nothing to fear here: Dolphins up for finals audition](https://www.nrl.com/news/2026/08/29/dolphins-embrace-top-four-test-against-chooks-in-run-to-finals/)  
  `nrl_news` 2026-08-28T21:01:21+00:00
- [NRL 2026: Confirmed lineups, results for Round 26 - sportingnews.com](https://www.sportingnews.com/au/rugby-league/news/nrl-team-lists-round-26-2026-lineups-injuries-results/f63f8b323e417cdfa9e267fc)  
  `google_news_rss` 2026-08-28T18:55:27+00:00
- [24 Hour Update | Round 26 v Dolphins - Sydney Roosters](https://www.roosters.com.au/news/2026/08/28/nrl-team-list--round-26-v-dolphins/)  
  `google_news_rss` 2026-08-28T06:01:00+00:00
- [Roosters vs Dolphins Preview & Betting Tips: NRL Round 26 2026 - Before You Bet](https://www.beforeyoubet.com.au/roosters-vs-dolphins-preview-betting-tips-nrl-round-26-2026)  
  `google_news_rss` 2026-08-27T07:00:00+00:00
- [Roosters v Dolphins: Round 26 - NRL.com](https://www.nrl.com/news/2026/08/26/roosters-v-dolphins-round-26/)  
  `google_news_rss` 2026-08-26T05:17:41+00:00
- [Wests Tigers NRL Injury Report: Round 26 - Wests Tigers](https://www.weststigers.com.au/news/2026/08/25/wests-tigers-injury-report-round-26/)  
  `google_news_rss` 2026-08-25T04:28:00+00:00
- [Live Blog Super Saturday: We stand with Jai at Cbus Super Presented by 6 mins ago](https://www.nrl.com/news/2026/08/29/super-saturday-we-stand-with-jai-at-cbus-super/)  
  `nrl_news` 2026-08-29T04:25:59+00:00
- [Joey’s major concern for Roosters in ‘make or break’ clash - Nine.com.au](https://www.nine.com.au/sport/nrl/news-sydney-roosters-dolphins-preview-andrew-johns-exclusive-comments-top-four-finals-premiership-20260828-p60sit.html)  
  `google_news_rss` 2026-08-28T20:57:24+00:00

## Queries the agent wrote

- `Roosters NRL injury OR "late mail" OR "team list" round 26`
- `Dolphins NRL injury OR "late mail" OR "team list" round 26`
- `Roosters vs Dolphins NRL round 26 preview`
- `Roosters Dolphins NRL odds OR price OR favourite`
- `Roosters Dolphins NRL finals race OR ladder stakes`
- `Roosters Dolphins NRL`
- `Roosters NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Dolphins NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Roosters Dolphins NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 26 Roosters OR Dolphins`

## Loops

- **Research refine**: not needed (gate passed: True, 17 items with body text)
- **Verifier**: coded checklist passed, LLM audit passed
    - no recalibration needed, so the judgement stands as first written

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | Tedesco's ankle injury is in nrl_news; Dolphins' 4-game streak is in scene; Roosters' loss to Tigers is in duckduckgo; ladder positions are in scene; bookmaker favorites are in google_news_rss. |
| `availability_direction` | pass | Tedesco is described as returning, which matches the source 'set to make his comeback'. |
| `shap_attribution` | pass | Bradley-Terry strength advantage is correctly attributed to the Roosters. |
| `weather_not_headline` | pass | Weather is not mentioned as a key factor. |
| `research_used` | pass | Key factor 2 is sourced from research (Tedesco injury). |
| `confidence_justified` | pass | Confidence (0.6) is a slight downward adjustment from the math prior (0.603) to account for Dolphins' momentum. |
| `driver_proportionality` | pass | The most significant driver (Bradley-Terry) is highlighted as the primary math factor. |
| `omitted_math_signals` | pass | Material drivers are Bradley-Terry (named) and 5-game form (alluded to via 'strong form' and 'momentum'). |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.