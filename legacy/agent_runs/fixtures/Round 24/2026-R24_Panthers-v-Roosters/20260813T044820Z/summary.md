# Panthers v Roosters

- **Run**: `20260813T044820Z-c5568e72`
- **When**: 2026-08-13T04:48:20.743141+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-13T19:50:00+10:00 at CommBank Stadium (round 24)

## Verdict

**Panthers** to win, confidence 60%.

> The Panthers hold a statistical edge in Elo and Bradley-Terry ratings, though confidence is tempered by their recent inconsistent form compared to the Roosters' five-game winning streak. Both teams face critical losses with James Tedesco (Roosters) and Isaah Yeo (Panthers) ruled out of this top-of-the-table clash.

### Key factors

- **math** — The model favours a home win based on an Elo rating advantage (+7 points), Bradley-Terry strength advantage, and superior ladder points differential per game.
- **research** — Roosters fullback James Tedesco has been ruled out of the match due to an ankle injury, with Cody Ramsey replacing him (nrl_news).
- **research** — Panthers captain Isaah Yeo is sidelined for four weeks following a pectoral injury sustained against the Warriors (nrl_news).

**Disagreement with the model:** The model probability (0.66) likely overstates the edge given the Roosters' current 5-game winning streak and the critical loss of captain Isaah Yeo for Penrith.

## What the maths said

- Prediction: **Home Win**
- P(Panthers win) = **0.6595**

| Favouring Panthers (home) | Favouring Roosters (away) |
| --- | --- |
| Bradley-Terry strength advantage (+0.29 log-strength) — contribution 0.148 (16% of total) | 5-game form: all run metres (-77.00) — contribution 0.041 (4% of total) |
| Ladder points differential per game (+8.1 points) — contribution 0.129 (14% of total) | 3-game form: errors (-1.33) — contribution 0.035 (4% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Elo rating advantage (+7 points) — contribution 0.054 (6% of total) | Away rest (14.0 days) — contribution 0.031 (3% of total) |
| Away travel to venue (23 km) — contribution 0.053 (6% of total) | Travel-distance advantage (-5 km for away) — contribution 0.029 (3% of total) |
| Head-to-head record (last 5) (80% to the home side) — contribution 0.038 (4% of total) | 5-game momentum: last20 net points (-15.00) — contribution 0.025 (3% of total) |

- Attribution balance: leans **home** (home 0.6302, away 0.3207)
- Value/contribution conflicts:
  - 3-game form: errors (-1.33)

## Ladder standings

As at round 24 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=24)).

- **Panthers** — 1th · 15-0-5 · PD +292 (+14.60/g)
- **Roosters** — 2th · 15-0-5 · PD +157 (+7.85/g)

- Higher on ladder: **Panthers**
- Points-difference favours: **Panthers** (home−away PD/game gap: 6.75)

## What the research found

18 items kept (dropped: stale 52, wrong_round 5, noise 8, irrelevant 11, duplicate_url 2, no_body 5).

- [NRL Late Mail: Round 24 - Teddy ruled out; Knights stars return](https://www.nrl.com/news/2026/08/12/nrl-late-mail-round-24---teddy-races-clock-knights-stars-return/)  
  `nrl_news` 2026-08-12T09:57:05+00:00
- [NRL Team Lists: Round 24](https://www.nrl.com/news/2026/08/11/nrl-team-lists-round-24/)  
  `nrl_news` 2026-08-11T05:59:00+00:00
- [Injuries NRL Casualty Ward: Fresh Reynolds injury; Roosters' Teddy blow 7 mins ago](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-08-13T04:41:35+00:00
- [Panthers v Roosters: Round 24 - NRL.com](https://www.nrl.com/news/2026/08/12/panthers-v-roosters-round-24/)  
  `google_news_rss` 2026-08-13T02:04:31+00:00
- [NRL News Jenkins to unleash hidden talent in Nawaqanitawase aerial contest](https://www.nrl.com/news/2026/08/13/jenkins-to-unleash-hidden-talent-in-nawaqanitawase-aerial-contest/)  
  `nrl_news` 2026-08-12T20:01:21+00:00
- [Panthers vs Roosters Preview & Betting Tips: NRL Round 24 2026 - Before You Bet](https://www.beforeyoubet.com.au/panthers-vs-roosters-preview-betting-tips-nrl-round-24-2026)  
  `google_news_rss` 2026-08-12T13:16:12+00:00
- [Panthers v Roosters: Edwards in the frame; Teddy struck down](https://www.nrl.com/news/2026/08/11/panthers-v-roosters-edwards-in-the-frame-teddys-ready/)  
  `nrl_news` 2026-08-12T10:00:26+00:00
- [NRL Coach Media | Round 24 v Panthers - Sydney Roosters](https://www.roosters.com.au/news/2026/08/12/nrl-coach-media--round-24-v-panthers/)  
  `google_news_rss` 2026-08-12T02:23:14+00:00
- [NRL News Ready to roar: Dramatic week driving Panthers towards Roosters showdown](https://www.nrl.com/news/2026/08/12/ready-to-roar-dramatic-week-driving-panthers-towards-roosters-showdown/)  
  `nrl_news` 2026-08-11T22:01:20+00:00
- [NRL News Roosters eye statement win in Penrith showdown](https://www.nrl.com/news/2026/08/11/roosters-eye-statement-win-in-penrith-showdown/)  
  `nrl_news` 2026-08-10T20:01:21+00:00
- [NRL Team Lists Round 24: Big ins, surprise calls and every confirmed squad - Zero Tackle](https://www.zerotackle.com/round-24-team-lists-2026-236834/)  
  `google_news_rss` 2026-08-13T04:17:05+00:00
- [NRL 2026 team lists: Every club's confirmed lineup for Round 24 - sportingnews.com](https://www.sportingnews.com/au/rugby-league/news/nrl-team-lists-round-24-2026-lineups-injuries-results/6511ddaebad07f3a28a97529)  
  `google_news_rss` 2026-08-12T10:08:15+00:00
- [NRL Updated Team List: Round 24 - Penrith Panthers](https://www.penrithpanthers.com.au/news/2026/08/12/nrl-updated-team-list-round-24/)  
  `google_news_rss` 2026-08-12T09:49:00+00:00
- [Reynolds’ cryptic reply as brutal setback revealed; Roosters’ big Teddy blow — Late Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-round-24-early-mail-news-teams-ins-and-outs-james-tedesco-in-doubt-dylan-edwards-pushing-to-play/news-story/ed6f741082a0959e49bf6a7f245bde8c)  
  `google_news_rss` 2026-08-12T10:28:11+00:00
- [Sea Eagles vs Dolphins Preview & Betting Tips: NRL Round 24 2026 - Before You Bet](https://www.beforeyoubet.com.au/sea-eagles-vs-dolphins-preview-betting-tips-nrl-round-24-2026)  
  `google_news_rss` 2026-08-13T03:33:43+00:00
- [Penrith Panthers vs Sydney Roosters Prediction, Tips & Odds - Ladbrokes](https://www.ladbrokes.com.au/blog/2026/08/13/penrith-panthers-vs-sydney-roosters-predictions/)  
  `google_news_rss` 2026-08-12T15:27:15+00:00
- [NRL Round 24 teams: Raiders star axed over ‘brain explosion’ - News.com.au](https://www.news.com.au/sport/nrl/nrl-teams-round-24-eels-star-isaiah-iongi-ruled-out-for-the-season/news-story/3e8f2b9ef18a7a662bffef54b8bf3d18)  
  `google_news_rss` 2026-08-12T11:50:56+00:00
- [2026 NRL Round 24 Predictions - Ladbrokes](https://www.ladbrokes.com.au/blog/2026/08/12/2026-nrl-round-24-predictions/)  
  `google_news_rss` 2026-08-12T05:02:46+00:00

## Queries the agent wrote

- `Panthers NRL injury OR "late mail" OR "team list" round 24`
- `Roosters NRL injury OR "late mail" OR "team list" round 24`
- `Panthers vs Roosters NRL round 24 preview`
- `Panthers Roosters NRL odds OR price OR favourite`
- `Panthers Roosters NRL finals race OR ladder stakes`
- `Panthers Roosters NRL`
- `Panthers NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Roosters NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Panthers Roosters NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 24 Panthers OR Roosters`

## Loops

- **Research refine**: not needed (gate passed: True, 18 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The market price of $1.77 is hallucinated as it does not appear in the provided tool outputs.
    - The top math driver 'Elo rating advantage (+7 points)' was omitted from the evaluation.
    - recalibrated: home 0.6 → home 0.6

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | fail | The claim that Panthers are market favourites at '$1.77' does not appear in any research body excerpt or scene field. |
| `availability_direction` | pass | Tedesco and Yeo are correctly described as ruled out/sidelined per the nrl_news excerpts. |
| `shap_attribution` | pass | Bradley-Terry strength and ladder points differential are correctly attributed to the Panthers from the favouring_Panthers_home_win group. |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factors include injuries to Tedesco and Yeo sourced from nrl_news. |
| `confidence_justified` | pass | Confidence of 0.6 is justified by the Roosters' winning streak and the loss of Isaah Yeo. |
| `driver_proportionality` | pass | The most significant SHAP drivers (Bradley-Terry and points differential) are the ones highlighted. |
| `omitted_math_signals` | fail | Top driver 'Elo rating advantage (+7 points)' is not named or alluded to in the judgement. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.