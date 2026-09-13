# Warriors v Dolphins

- **Run**: `20260911T211252Z-7ce081d8`
- **When**: 2026-09-11T21:12:52.881022+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-09-12T16:05:00+10:00 at Go Media Stadium (round 28)

## Verdict

**Warriors** to win, confidence 60%.

> The Warriors hold a modest edge as the second-placed side hosting the third-placed Dolphins. The model's preference is driven by superior points differential and Pythagorean form, while the Warriors receive a boost from the return of forward Jackson Ford. Despite the Dolphins' seven-game winning streak, the Warriors' strong home record (10-2) and ladder advantage provide a slight edge.

### Key factors

- **math** — The model's strongest drivers are the ladder points differential per game (16% contribution) and Pythagorean form over the last 10 games (12% contribution), both favouring the Warriors.
- **research** — The Warriors receive a significant boost with gun forward Jackson Ford returning from a pectoral injury (nrl_news).
- **scene** — The Warriors are higher on the official ladder (2nd vs 3rd) and maintain a dominant home record of 10-2.

## What the maths said

- Prediction: **Home Win**
- P(Warriors win) = **0.5858**

| Favouring Warriors (home) | Favouring Dolphins (away) |
| --- | --- |
| Ladder points differential per game (+6.8 points) — contribution 0.140 (16% of total) | 5-game momentum: penalty cluster rate (-1.60) — contribution 0.092 (10% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Pythagorean form (last 10) (+25% expected-win gap) — contribution 0.107 (12% of total) | 5-game form: all run metres (+2.40) — contribution 0.037 (4% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Elo rating advantage (-10 points) — contribution 0.039 (4% of total); CONFLICT: the raw value on its own favours the away side — the model still nets it toward home here | 5-game form: points for (+10.20) — contribution 0.034 (4% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| 5-game workload: top3 tackle share (-0.01) — contribution 0.021 (2% of total) | 3-game form: errors (-2.00) — contribution 0.029 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| 5-game form: tackle breaks (+8.60) — contribution 0.019 (2% of total) | 5-game form: penalties conceded (-2.40) — contribution 0.029 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |

- Attribution balance: leans **home** (home 0.4577, away 0.4396)
- Value/contribution conflicts:
  - Elo rating advantage (-10 points)
  - 5-game momentum: penalty cluster rate (-1.60)
  - 5-game form: all run metres (+2.40)
  - 5-game form: points for (+10.20)
  - 3-game form: errors (-2.00)
  - 5-game form: penalties conceded (-2.40)

## Ladder standings

As at round 28 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=28)).

- **Warriors** — 2th · 18-0-6 · PD +310 (+12.92/g)
- **Dolphins** — 3th · 17-0-7 · PD +156 (+6.50/g)

- Higher on ladder: **Warriors**
- Points-difference favours: **Warriors** (home−away PD/game gap: 6.42)

## What the research found

17 items kept (dropped: stale 67, wrong_round 3, noise 7, irrelevant 19, duplicate_url 3, no_body 5).

- ['Our biggest motivation': Top four sides out to follow proven path to premiership](https://www.nrl.com/news/2026/09/11/our-biggest-motivation-top-four-sides-out-to-follow-proven-path-to-premiership/)  
  `nrl_news` 2026-09-11T06:38:53+00:00
- [NRL Casualty Ward: Walker goes down with calf injury](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-09-11T10:46:41+00:00
- [NRL Late Mail: Finals Week 1 - Sharks lose Puru](https://www.nrl.com/news/2026/09/10/nrl-late-mail-finals-week-1/)  
  `nrl_news` 2026-09-11T10:05:17+00:00
- [Match Preview Warriors v Dolphins: Ford set to motor; Big Three return](https://www.nrl.com/news/2026/09/08/warriors-v-dolphins-ford-set-to-motor-big-three-return/)  
  `nrl_news` 2026-09-11T06:09:51+00:00
- [NRL Team Lists: Finals Week 1](https://www.nrl.com/news/2026/09/08/nrl-team-lists-finals-week-1/)  
  `nrl_news` 2026-09-08T05:59:00+00:00
- [Wayne’s Latrell warning as Knights boost confirmed; Sharks stars face final hurdle — Finals Late Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-finals-2026-week-1-team-news-injuries-changes-late-mail-who-is-in-and-out/news-story/19748a07cd154a6af4a7810773fdcf09)  
  `google_news_rss` 2026-09-11T08:24:27+00:00
- [Warriors v Dolphins NRL qualifying final: Kick-off time, team list, injuries - everything to know - RNZ](https://www.rnz.co.nz/news/sport/1335854/warriors-v-dolphins-nrl-qualifying-final-kick-off-time-team-list-injuries-everything-to-know)  
  `google_news_rss` 2026-09-11T01:21:54+00:00
- [Sharks v Dragons: Ravics returns; Half-centruy for Ciesiolka](https://www.nrl.com/news/2026/09/09/sharks-v-dragons-ravics-returns-half-centruy-for-ciesiolka/)  
  `nrl_news` 2026-09-11T07:13:52+00:00
- [New Zealand Warriors vs Dolphins Tips, Odds, Teams & Predictions – NRL Finals Week 1 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/new-zealand-warriors-vs-dolphins-tips-odds-teams-predictions-nrl-finals-week-1-2026/610221)  
  `google_news_rss` 2026-09-09T07:43:12+00:00
- [Wests Tigers v Raiders: Apps, Turnbull sidelined; Dodd in for Taufa](https://www.nrl.com/news/2026/09/08/wests-tigers-v-raiders-turnbull-good-to-go-dodd-in-for-taufa/)  
  `nrl_news` 2026-09-11T06:14:16+00:00
- [Match Preview: Qualifying Final – Dolphins v Warriors - Official website of The Dolphins](https://www.dolphinsnrl.com.au/news/2026/09/11/match-preview-qualifying-final--dolphins-v-warriors/)  
  `google_news_rss` 2026-09-11T04:22:27+00:00
- [Warriors vs Dolphins Preview & Betting Tips: 2026 NRL Qualifying Final - Before You Bet](https://www.beforeyoubet.com.au/warriors-vs-dolphins-preview-betting-tips-2026-nrl-qualifying-final)  
  `google_news_rss` 2026-09-11T03:59:24+00:00
- [Warriors Webster targets 'simple fixes' as Wahs tune up for tilt at history](https://www.nrl.com/news/2026/09/10/webster-targets-simple-fixes-as-wahs-tune-up-for-tilt-at-history/)  
  `nrl_news` 2026-09-10T04:01:23+00:00
- [Dolphins Fit and firing forward pack a key factor in Phins finals push](https://www.nrl.com/news/2026/09/10/fit-and-firing-forward-pack-a-key-factor-in-phins-finals-push/)  
  `nrl_news` 2026-09-10T02:01:24+00:00
- [Resold tickets for Warriors v Dolphins could be cancelled, Ticketmaster warns](https://www.rnz.co.nz/news/sport/1340580/resold-tickets-for-warriors-v-dolphins-could-be-cancelled-ticketmaster-warns)  
  `duckduckgo` 2026-09-09T21:13:43+00:00
- [Warriors Wandering Warriors have seen it all on the road to the Holy Grail](https://www.nrl.com/news/2026/09/09/wandering-warriors-have-seen-it-all-on-the-road-to-the-holy-grail/)  
  `nrl_news` 2026-09-08T23:01:21+00:00
- [Dolphins 'We can win it': Hammer adamant Phins up for finals fight](https://www.nrl.com/news/2026/09/07/we-can-win-it-hammers-high-confidence-in-phins-chances/)  
  `nrl_news` 2026-09-07T07:01:21+00:00

## Queries the agent wrote

- `Warriors NRL injury OR "late mail" OR "team list" round 28`
- `Dolphins NRL injury OR "late mail" OR "team list" round 28`
- `Warriors vs Dolphins NRL round 28 preview`
- `Warriors Dolphins NRL odds OR price OR favourite`
- `Warriors Dolphins NRL finals race OR ladder stakes`
- `Warriors Dolphins NRL`
- `Warriors NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Dolphins NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Warriors Dolphins NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 28 Warriors OR Dolphins`

## Loops

- **Research refine**: not needed (gate passed: True, 17 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - Hallucinated market odds of $1.55.
    - Omitted several top math drivers, most notably 'Pythagorean form (last 10)' (12%).
    - recalibrated: home 0.6 → home 0.6

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | fail | The claim 'Market odds ($1.55)' does not appear in any research body_excerpt; the closest mention is 'around a converted try favourite'. |
| `availability_direction` | pass | Jackson Ford is described as returning, which matches the research stating he is 'set to return from a pectoral injury'. |
| `shap_attribution` | pass | Ladder points differential per game is correctly attributed to the Warriors (home win). |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factor 2 identifies the return of Jackson Ford from nrl_news. |
| `confidence_justified` | pass | Confidence of 0.6 is defensible for a close matchup between 2nd and 3rd placed teams both on winning streaks. |
| `driver_proportionality` | pass | The most significant SHAP driver (16%) is the primary math factor used. |
| `omitted_math_signals` | fail | Top drivers 'Pythagorean form (last 10)' (12%) and 'Elo rating advantage' (4%) for the Warriors, and 'all run metres' (4%) and 'points for' (4%) for the Dolphins are not addressed. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.