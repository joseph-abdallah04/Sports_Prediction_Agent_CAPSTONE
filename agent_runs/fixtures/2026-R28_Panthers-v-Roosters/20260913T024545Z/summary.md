# Panthers v Roosters

- **Run**: `20260913T024545Z-3961c051`
- **When**: 2026-09-13T02:45:45.741281+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-09-13T16:05:00+10:00 at CommBank Stadium (round 28)

## Verdict

**Panthers** to win, confidence 68%.

> The Panthers hold a strong math prior and minor premiership advantage, which is further reinforced by critical availability news. The Roosters are severely hampered by the absence of star halfback Sam Walker and second-rower Angus Crichton (nrl_news), while the Panthers welcome back Isaah Yeo and Scott Sorensen (sportsnews.com.au). This, combined with the Roosters' current three-game losing streak, justifies a confidence level above the math prior.

- **Research vs math:** confirms
- **Strongest reason it could lose:** The Roosters defeated the Panthers 12-6 in their most recent encounter in Round 24.
- **Loss reason is specific:** True

### Key factors

- **math** — The model favours the Panthers based on a Bradley-Terry strength advantage and a significant ladder points differential per game.
- **research** — The Roosters will be without Sam Walker (ankle) and Angus Crichton (foot), forcing an inexperienced halves pairing of Daly Cherry-Evans and Hugo Savala (nrl_news).
- **research** — The Panthers are bolstered by the return of Isaah Yeo to the starting side and Scott Sorensen from a calf injury (sportsnews.com.au).

## What the maths said

- Prediction: **Home Win**
- P(Panthers win) = **0.6361**

| Favouring Panthers (home) | Favouring Roosters (away) |
| --- | --- |
| Bradley-Terry strength advantage (+0.29 log-strength) — contribution 0.155 (13% of total) | 5-game form: all run metres (-118.20) — contribution 0.089 (7% of total) |
| Ladder points differential per game (+7.0 points) — contribution 0.142 (12% of total) | Pythagorean form (last 10) (-19% expected-win gap) — contribution 0.065 (5% of total) |
| 5-game form: missed tackles (+11.60) — contribution 0.085 (7% of total); CONFLICT: the raw value on its own favours the away side — the model still nets it toward home here | 3-game form: kicking metres (+140.67) — contribution 0.061 (5% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Elo rating advantage (+13 points) — contribution 0.052 (4% of total) | Travel-distance advantage (-5 km for away) — contribution 0.045 (4% of total) |
| Away travel to venue (23 km) — contribution 0.048 (4% of total) | 3-game form: errors (-2.00) — contribution 0.027 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |

- Attribution balance: leans **home** (home 0.7115, away 0.4906)
- Value/contribution conflicts:
  - 5-game form: missed tackles (+11.60)
  - 3-game form: kicking metres (+140.67)
  - 3-game form: errors (-2.00)

## Ladder standings

As at round 28 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=28)).

- **Panthers** — 1th · 18-0-6 · PD +336 (+14.00/g)
- **Roosters** — 4th · 16-0-8 · PD +118 (+4.92/g)

- Higher on ladder: **Panthers**
- Points-difference favours: **Panthers** (home−away PD/game gap: 9.08)

## What the research found

17 items kept (dropped: stale 64, wrong_round 3, noise 8, irrelevant 34, evergreen_casualty_ward 1, roundup_no_fixture_team 1, duplicate_url 5, no_body 3).

- [On-field coach: How injury torment gave Kenny a unique outlook for finals bid](https://www.nrl.com/news/2026/09/10/on-field-coach-how-injury-torment-gave-kenny-a-unique-outlook-for-finals-bid/)  
  `nrl_news` 2026-09-10T04:01:23+00:00
- [Finals 'Our biggest motivation': Top four sides out to follow proven path to premiership](https://www.nrl.com/news/2026/09/11/our-biggest-motivation-top-four-sides-out-to-follow-proven-path-to-premiership/)  
  `nrl_news` 2026-09-11T06:38:53+00:00
- [Team Lists NRL Late Mail: Finals Week 1 - Crichton return hopes dashed](https://www.nrl.com/news/2026/09/10/nrl-late-mail-finals-week-1/)  
  `nrl_news` 2026-09-12T09:57:53+00:00
- ['Go out there and express myself': Hugo ready to rise to challenge](https://www.nrl.com/news/2026/09/13/go-out-there-and-express-myself-hugo-ready-to-rise-to-challenge/)  
  `nrl_news` 2026-09-12T20:01:21+00:00
- [Finals History lesson: Last time the contenders met in a final](https://www.nrl.com/news/2026/09/11/history-lesson-last-time-the-contenders-met-in-a-final/)  
  `nrl_news` 2026-09-11T06:42:46+00:00
- [Finals Marky Mark making every moment count in run to the finish](https://www.nrl.com/news/2026/09/11/marky-mark-making-every-moment-count-in-run-to-the-finish/)  
  `nrl_news` 2026-09-11T04:01:21+00:00
- [Match Preview Panthers v Roosters: Yeo locked in; Big guns set for return](https://www.nrl.com/news/2026/09/08/panthers-v-roosters-yeo-locked-in-big-guns-set-for-return/)  
  `nrl_news` 2026-09-08T09:01:22+00:00
- [Injury returns, Roosters form, Panthers unstoppable?: The FIVE biggest questions for the NRL finals - Zero Tackle](https://www.zerotackle.com/injury-returns-roosters-form-panthers-unstoppable-the-five-biggest-questions-for-the-nrl-finals-237849/)  
  `google_news_rss` 2026-09-10T20:44:37+00:00
- [Roosters’ bumper halves boost; Cowboys’ late switch as star returns: NRL Late Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-finals-2026-week-1-team-news-injuries-changes-late-mail-who-is-in-and-out/news-story/19748a07cd154a6af4a7810773fdcf09)  
  `google_news_rss` 2026-09-12T08:28:38+00:00
- [NRL Updated Team List: Finals Week 1 - Penrith Panthers](https://www.penrithpanthers.com.au/news/2026/09/12/nrl-updated-team-list-finals-week-1/)  
  `google_news_rss` 2026-09-12T06:04:00+00:00
- [Penrith Panthers vs Sydney Roosters Tips, Odds, Teams & Predictions – NRL Finals Week 1 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/penrith-panthers-vs-sydney-roosters-tips-odds-teams-predictions-nrl-finals-week-1-2026/610223)  
  `google_news_rss` 2026-09-09T07:44:45+00:00
- [Team Lists NRL Team Lists: Finals Week 1](https://www.nrl.com/news/2026/09/08/nrl-team-lists-finals-week-1/)  
  `nrl_news` 2026-09-08T05:59:00+00:00
- [Penrith Panthers v Sydney Roosters - Finals week 1, 2026 - NRL Score Centre - Live NRL Scores - ABC News & Headlines – Australian Broadcasting Corporation](https://www.abc.net.au/news/sport/score-centre/nrl/2026-09-13/panthers-roosters/231203312)  
  `google_news_rss` 2026-09-12T13:52:45+00:00
- [Panthers vs Roosters Preview & Betting Tips: 2026 NRL Qualifying Final - beforeyoubet.com.au](https://www.beforeyoubet.com.au/panthers-vs-roosters-preview-betting-tips-2026-nrl-qualifying-final)  
  `google_news_rss` 2026-09-12T08:20:17+00:00
- [The Roosters’ wheels came off at exactly the wrong time. Can they go back to the future? - SMH.com.au](https://www.smh.com.au/sport/nrl/the-roosters-wheels-came-off-at-exactly-the-wrong-time-can-they-go-back-to-the-future-20260910-p60w0q.html)  
  `google_news_rss` 2026-09-12T03:30:00+00:00
- [Dolphins down Warriors 26-16 to reach preliminary finals](https://www.fijivillage.com/news/dolphins-down-warriors-26-16-to-reach-preliminary-finals-f5bbf5/)  
  `duckduckgo` 2026-09-11T02:46:34+00:00
- [Panthers v Roosters: Finals Week 1 - NRL.com](https://www.nrl.com/watch/news/panthers-v-roosters-finals-week-1-1990286/)  
  `google_news_rss` 2026-09-09T05:51:19+00:00

## Queries the agent wrote

- `Panthers NRL injury OR "late mail" OR "team list" round 28`
- `Roosters NRL injury OR "late mail" OR "team list" round 28`
- `Panthers vs Roosters NRL round 28 preview`
- `Panthers Roosters NRL odds OR price OR favourite`
- `Panthers Roosters NRL finals race OR ladder stakes`
- `Panthers Roosters NRL`
- `Panthers NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Roosters NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Panthers Roosters NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 28 Panthers OR Roosters`

## Loops

- **Research refine**: not needed (gate passed: True, 17 items with body text)
- **Verifier**: coded checklist passed, LLM audit passed
    - no recalibration needed, so the judgement stands as first written

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | Matched Sam Walker (ankle) and Angus Crichton (foot) to nrl_news; Yeo, Sorensen (calf), and Roosters 3-game streak to sportsnews.com.au; Round 24 result to sportsnews.com.au. |
| `availability_direction` | pass | Walker and Crichton are correctly described as absent; Yeo and Sorensen are correctly described as returning. |
| `shap_attribution` | pass | Bradley-Terry strength and ladder points differential are correctly attributed to the Panthers from the favouring_Panthers_home_win group. |
| `weather_not_headline` | pass | Weather is not mentioned as a key factor. |
| `research_used` | pass | Key factors include research from nrl_news and sportsnews.com.au. |
| `confidence_justified` | pass | Confidence (0.68) is slightly above the math prior (0.6361), justified by specific availability losses for Roosters and returns for Panthers. |
| `driver_proportionality` | pass | The judgement focuses on the top material SHAP drivers and research, not minor factors. |
| `omitted_math_signals` | pass | Both material drivers (Bradley-Terry strength and Ladder points differential) are explicitly named in the first key factor. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.