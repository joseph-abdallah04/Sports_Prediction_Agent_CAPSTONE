# Raiders v Knights

- **Run**: `20260809T005509Z-be2ac1aa`
- **When**: 2026-08-09T00:55:09.849730+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-09T14:00:00+10:00 at GIO Stadium (round 23)

## Verdict

**Knights** to win, confidence 60%.

> The Knights hold a significant advantage in the standings (7th vs 12th) and points differential (+60 vs -59), supported by superior recent form including a dominant win over Brisbane. While math drivers such as Bradley-Terry strength and Elo ratings suggest a latent ability edge for the Raiders, the overall attribution balance leans toward Newcastle despite the loss of Bradman Best to injury.

### Key factors

- **scene** — The Knights are significantly higher on the ladder (7th) than the Raiders (12th), with a points differential of +60 compared to the Raiders' -59.
- **research** — Newcastle enters following an emphatic 30-6 win over Brisbane, whereas Canberra was comprehensively beaten 42-18 by Penrith (BeforeYouBet); however, Newcastle will miss Bradman Best due to a calf strain (nrl.com).
- **math** — While the Bradley-Terry strength advantage (+0.35 log-strength) and Elo rating (+19 points) favor the Raiders, the total attribution balance leans away (-0.1353 net), favoring the Knights.

**Disagreement with the model:** The model predicts a Home Win (0.5491), but I am picking Away because the official standings and recent form strongly outweigh the latent strength indicators (Elo/Bradley-Terry) cited by the model.

## What the maths said

- Prediction: **Home Win**
- P(Raiders win) = **0.5491**

| Favouring Raiders (home) | Favouring Knights (away) |
| --- | --- |
| Bradley-Terry strength advantage (+0.35 log-strength) — contribution 0.120 (16% of total) | Pythagorean form (last 10) (-12% expected-win gap) — contribution 0.060 (8% of total) |
| Elo rating advantage (+19 points) — contribution 0.056 (8% of total) | 5-game form: points for (+13.00) — contribution 0.048 (7% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Head-to-head record (last 5) (60% to the home side) — contribution 0.036 (5% of total) | 3-game form: errors (-1.67) — contribution 0.033 (5% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Home travel to venue (0 km) — contribution 0.013 (2% of total) | Ladder points differential per game (-6.0 points) — contribution 0.024 (3% of total) |
| 5-game momentum: penalty cluster rate (+0.40) — contribution 0.012 (2% of total); CONFLICT: the raw value on its own favours the away side — the model still nets it toward home here | 5-game form: all run metres (+11.80) — contribution 0.023 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |

- Attribution balance: leans **away** (home 0.2959, away 0.4311)
- Value/contribution conflicts:
  - 5-game momentum: penalty cluster rate (+0.40)
  - 5-game form: points for (+13.00)
  - 3-game form: errors (-1.67)
  - 5-game form: all run metres (+11.80)

## Ladder standings

As at round 23 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=23)).

- **Raiders** — 12th · 9-0-11 · PD -59 (-2.95/g)
- **Knights** — 7th · 12-0-8 · PD +60 (+3.00/g)

- Higher on ladder: **Knights**
- Points-difference favours: **Knights** (home−away PD/game gap: -5.95)

## What the research found

17 items kept (dropped: stale 59, wrong_round 4, noise 17, irrelevant 15, duplicate_url 2, no_body 6).

- [Team Lists NRL Late Mail: Round 23 - Best sidelined](https://www.nrl.com/news/2026/08/05/nrl-late-mail-round-23---origin-guns-return-as-finals-loom/)  
  `nrl_news` 2026-08-08T09:52:49+00:00
- [Team Lists NRL Team Lists: Round 23](https://www.nrl.com/news/2026/08/04/nrl-team-lists-round-23/)  
  `nrl_news` 2026-08-04T06:00:45+00:00
- [NRL Casualty Ward: Panthers' Yeo blow; Ward, Iongi, Tupouniua felled](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-08-08T12:22:04+00:00
- [Raiders vs Knights Preview & Betting Tips: NRL Round 23 2026 - Before You Bet](https://www.beforeyoubet.com.au/raiders-vs-knights-preview-betting-tips-nrl-round-23-2026)  
  `google_news_rss` 2026-08-07T16:39:46+00:00
- [Raiders v Knights: Round 23 - nrl.com](https://www.nrl.com/news/2026/08/05/raiders-v-knights-round-23/)  
  `google_news_rss` 2026-08-05T04:05:26+00:00
- [Raiders vs Knights - Round 23, 2026 - Live Scores & Stats - Match Centre - Zero Tackle](https://www.zerotackle.com/raiders-knights-round-23-2026-mc10396512-236512/)  
  `google_news_rss` 2026-08-02T18:36:21+00:00
- [Wests Tigers NRL Injury Report: Round 23 - Wests Tigers](https://www.weststigers.com.au/news/2026/08/06/Wests-Tigers-NRL-Injury-Report-Round-23/)  
  `google_news_rss` 2026-08-06T00:30:30+00:00
- [NRL Team List | Round 23 - Newcastle Knights](https://www.newcastleknights.com.au/news/2026/08/04/nrl-team-list--round-23/)  
  `google_news_rss` 2026-08-04T06:01:22+00:00
- [NRL Team Lists Round 23: Big ins, surprise calls and every confirmed squad - Zero Tackle](https://www.zerotackle.com/round-23-team-lists-2026-236562/)  
  `google_news_rss` 2026-08-04T05:58:19+00:00
- [Knights lose star back; Wayne confirms crushing Souths blow after training mishap — Late Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-jeremiah-nanai-ruled-out-with-hamstring-injury-surprising-reason-dylan-walker-was-omitted-jonah-pezet-injured-early-mail-team-news-nrl-news/news-story/8b1bcfbd343d2d6947ed218f030cfe66)  
  `google_news_rss` 2026-08-08T08:41:42+00:00
- [NRL Team List: Raiders v Knights - raiders.com.au](https://www.raiders.com.au/news/2026/08/04/nrl-team-list-raiders-v-knights/)  
  `google_news_rss` 2026-08-04T05:56:16+00:00
- [NRL 2026: Confirmed lineups, results for Round 23 - sportingnews.com](https://www.sportingnews.com/au/rugby-league/news/nrl-team-lists-round-23-2026-lineups-injuries-results/b358f066284f90e03d93a242)  
  `google_news_rss` 2026-08-08T19:17:02+00:00
- [NRL News /](https://www.nrl.com/news/topic/nrl-news/)  
  `duckduckgo` 2026-08-08T12:22:00+00:00
- [2026 NRL Round 23 Predictions - Ladbrokes](https://www.ladbrokes.com.au/blog/2026/08/05/2026-nrl-round-23-predictions/)  
  `google_news_rss` 2026-08-04T23:57:46+00:00
- [Match Preview Dolphins v Broncos: Katoa ready to shine; Duffy steps up](https://www.nrl.com/news/2026/08/04/dolphins-v-broncos-katoa-ready-to-shine-duffy-steps-up/)  
  `nrl_news` 2026-08-08T06:04:31+00:00
- [Knights cop unwanted blow with Bradman Best ruled out of Raiders clash - 7NEWS](https://7news.com.au/sport/rugby-league/knights-cop-unwanted-blow-with-bradman-best-ruled-out-of-raiders-clash-c-22695500)  
  `google_news_rss` 2026-08-08T05:45:00+00:00
- [Raiders v Knights: Sasagi returns; Frizell the milestone man - nrl.com](https://www.nrl.com/news/2026/08/04/raiders-v-knights-sasagi-returns-frizell-the-milestone-man/)  
  `google_news_rss` 2026-08-08T04:06:56+00:00

## Queries the agent wrote

- `Raiders NRL injury OR "late mail" OR "team list" round 23`
- `Knights NRL injury OR "late mail" OR "team list" round 23`
- `Raiders vs Knights NRL round 23 preview`
- `Raiders Knights NRL odds OR price OR favourite`
- `Raiders Knights NRL finals race OR ladder stakes`
- `Raiders Knights NRL`
- `Raiders NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Knights NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Raiders Knights NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 23 Raiders OR Knights`

## Loops

- **Research refine**: not needed (gate passed: True, 17 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The top math signals favouring the Raiders (Bradley-Terry strength advantage and Elo rating advantage) were omitted from the analysis.
    - recalibrated: away 0.6 → away 0.6

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | Standings/diff matched to set_fixture_scene; Bradman Best injury matched to nrl_news body excerpt; Brisbane win matched to google_news_rss excerpt. |
| `availability_direction` | pass | Bradman Best is correctly described as missing based on research stating he is 'without' and suffered a calf strain. |
| `shap_attribution` | pass | Pythagorean form and ladder points differential are both listed in the favouring_Knights_away_win group. |
| `weather_not_headline` | pass | Weather (Rain) is not mentioned as a factor in the judgement. |
| `research_used` | pass | Key factor identifies Bradman Best's injury sourced from research (nrl.com). |
| `confidence_justified` | pass | Confidence of 0.6 is defensible given the disagreement with the model's prediction and the away-win nature of the pick. |
| `driver_proportionality` | pass | The judgement focuses on the net attribution balance and top drivers (Pythagorean form) rather than minor factors. |
| `omitted_math_signals` | fail | Top Raiders drivers 'Bradley-Terry strength advantage' and 'Elo rating advantage' are not named or alluded to in the evaluation. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.