# Sharks v Cowboys

- **Run**: `20260911T213251Z-7f3ddb01`
- **When**: 2026-09-11T21:32:51.326334+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-09-12T19:50:00+10:00 at Allianz Stadium (round 28)

## Verdict

**Sharks** to win, confidence 72%.

> The Sharks hold a clear edge based on a strong math prior (0.76 probability) and a market price of $1.44 (sportsnews.com.au). While the Cowboys benefit from 14 days of rest and the model notes the travel burden, these are outweighed by the Sharks' strength advantage and superior possession metrics. The return of the Hynes-Trindall halves pairing (sharks.com.au) further solidifies the home side's advantage despite their recent form slump.

### Key factors

- **math** — Strong Bradley-Terry strength advantage and superior 5-game possession percentage (each contributing ~13-14% to the home win prediction)
- **research** — Return of key players Nicho Hynes, Blayke Brailey, KL Iro, Teig Wilton, and Braydon Trindall (sharks.com.au)
- **scene** — Significant ladder advantage (5th vs 8th) and a points difference gap of 233 points (+149 for Sharks vs -84 for Cowboys)

## What the maths said

- Prediction: **Home Win**
- P(Sharks win) = **0.7649**

| Favouring Sharks (home) | Favouring Cowboys (away) |
| --- | --- |
| Bradley-Terry strength advantage (+0.40 log-strength) — contribution 0.173 (14% of total) | Away travel to venue (1,680 km) — contribution 0.024 (2% of total) |
| Ladder points differential per game (+9.4 points) — contribution 0.168 (14% of total) | 5-game form: penalties conceded (-1.80) — contribution 0.024 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| 5-game form: possession pct (+6.60) — contribution 0.160 (13% of total) | Away rest (14.0 days) — contribution 0.022 (2% of total) |
| Pythagorean form (last 10) (+40% expected-win gap) — contribution 0.116 (9% of total) | 5-game form: effective tackle pct (-1.41) — contribution 0.017 (1% of total) |
| Elo rating advantage (+46 points) — contribution 0.062 (5% of total) | 5-game momentum: penalty gap seconds (-29.82) — contribution 0.016 (1% of total) |

- Attribution balance: leans **home** (home 1.017, away 0.2003)
- Value/contribution conflicts:
  - 5-game form: penalties conceded (-1.80)

## Ladder standings

As at round 28 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=28)).

- **Sharks** — 5th · 14-0-10 · PD +149 (+6.21/g)
- **Cowboys** — 8th · 13-0-11 · PD -84 (-3.50/g)

- Higher on ladder: **Sharks**
- Points-difference favours: **Sharks** (home−away PD/game gap: 9.71)

## What the research found

20 items kept (dropped: stale 55, wrong_round 3, noise 11, irrelevant 19, duplicate_url 1, no_body 4).

- ['My last opportunity': Old school approach serving McInnes to the end](https://www.nrl.com/news/2026/09/12/could-be-my-last-game-mcinnes-sticking-to-old-school-approach-until-the-end/)  
  `nrl_news` 2026-09-11T20:01:21+00:00
- [NRL Casualty Ward: Walker goes down with calf injury](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-09-11T10:46:41+00:00
- [Sharks v Cowboys: Tricky treat for home fans; Nanai, Neame add punch](https://www.nrl.com/news/2026/09/08/sharks-v-cowboys-tricky-treat-for-home-fans-nanai-neame-add-punch/)  
  `nrl_news` 2026-09-11T10:06:02+00:00
- [NRL Late Mail: Finals Week 1 - Sharks lose Puru](https://www.nrl.com/news/2026/09/10/nrl-late-mail-finals-week-1/)  
  `nrl_news` 2026-09-11T10:05:17+00:00
- [Finals History lesson: Last time the contenders met in a final](https://www.nrl.com/news/2026/09/11/history-lesson-last-time-the-contenders-met-in-a-final/)  
  `nrl_news` 2026-09-11T06:42:46+00:00
- [Finals 'No one gave us a chance': Chasing pack desperate to defy history](https://www.nrl.com/news/2026/09/10/no-one-gave-us-a-chance-chasing-pack-desperate-to-defy-history/)  
  `nrl_news` 2026-09-11T06:40:01+00:00
- [The family heartbreak driving young Shark's finals bid](https://www.nrl.com/news/2026/09/11/the-family-heartbreak-driving-young-sharks-finals-bid/)  
  `nrl_news` 2026-09-11T02:01:22+00:00
- [NRL Team Lists: Finals Week 1](https://www.nrl.com/news/2026/09/08/nrl-team-lists-finals-week-1/)  
  `nrl_news` 2026-09-08T05:59:00+00:00
- [Updated Cowboys NRL team list: Elimination Final v Sharks - North Queensland Cowboys](https://www.cowboys.com.au/news/2026/09/11/updated-cowboys-nrl-team-list-elimination-final-v-sharks-at-allianz-stadium/)  
  `google_news_rss` 2026-09-11T09:50:00+00:00
- [NRL Team List: Week 1 Finals v Cowboys - sharks.com.au](https://www.sharks.com.au/news/2026/09/08/nrl-team-list-week-1-finals-v-cowboys/)  
  `google_news_rss` 2026-09-08T06:00:00+00:00
- [Cronulla Sharks vs North Queensland Cowboys Tips, Odds, Teams & Predictions – NRL Finals Week 1 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/cronulla-sharks-vs-north-queensland-cowboys-tips-odds-teams-predictions-nrl-finals-week-1-2026/610222)  
  `google_news_rss` 2026-09-09T07:44:45+00:00
- [Warriors v Dolphins: Ford set to motor; Big Three return](https://www.nrl.com/news/2026/09/08/warriors-v-dolphins-ford-set-to-motor-big-three-return/)  
  `nrl_news` 2026-09-11T06:09:51+00:00
- [How do you get from eighth to a grand final? ‘A prime Jason Taumalolo helps’ - SMH.com.au](https://www.smh.com.au/sport/nrl/how-do-you-get-from-eighth-to-a-grand-final-a-prime-jason-taumalolo-helps-20260910-p60w5l.html)  
  `google_news_rss` 2026-09-11T05:59:00+00:00
- [Sharks vs Cowboys Preview & Betting Tips: 2026 NRL Elimination Final - Before You Bet](https://www.beforeyoubet.com.au/sharks-vs-cowboys-preview-betting-tips-2026-nrl-elimination-final)  
  `google_news_rss` 2026-09-11T03:59:24+00:00
- [NRL Match Preview: Week 1 Finals v Cowboys - sharks.com.au](https://www.sharks.com.au/news/2026/09/11/nrl-match-preview-week-1-finals-v-cowboys/)  
  `google_news_rss` 2026-09-11T03:50:00+00:00
- [‘Anger, surprise, joy’: Coach’s wild ride to the finals - News.com.au](https://www.news.com.au/sport/nrl/anger-surprise-and-then-joy-todd-payten-rides-the-emotional-rollercoaster-at-the-judiciary-says-50point-stat-is-ready-to-fall/news-story/1df950a905085749d11160487f60d3b9)  
  `google_news_rss` 2026-09-11T02:36:22+00:00
- [Cowboys 'We deserve to be here': Purdue backs Cowboys to make finals chance count](https://www.nrl.com/news/2026/09/10/we-deserve-to-be-here-purdue-backs-cowboys-to-make-finals-chance-count/)  
  `nrl_news` 2026-09-10T00:01:51+00:00
- [NRL Gameday Guide: Week 1 Finals v Cowboys - sharks.com.au](https://www.sharks.com.au/news/2026/09/09/nrl-gameday-guide-week-1-finals-v-cowboys/)  
  `google_news_rss` 2026-09-09T07:00:00+00:00
- [Trindall ready to spark Sharks in high-stakes comeback](https://www.nrl.com/news/2026/09/08/trindall-ready-to-spark-sharks-in-high-stakes-comeback/)  
  `nrl_news` 2026-09-07T20:01:21+00:00
- [Sharks v Cowboys - Finals Week 1, 2026 - Match Centre - NRL.com](https://www.nrl.com/draw/nrl-premiership/2026/finals-week-1/sharks-v-cowboys/)  
  `google_news_rss` 2026-09-06T08:39:40+00:00

## Queries the agent wrote

- `Sharks NRL injury OR "late mail" OR "team list" round 28`
- `Cowboys NRL injury OR "late mail" OR "team list" round 28`
- `Sharks vs Cowboys NRL round 28 preview`
- `Sharks Cowboys NRL odds OR price OR favourite`
- `Sharks Cowboys NRL finals race OR ladder stakes`
- `Sharks Cowboys NRL`
- `Sharks NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Cowboys NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Sharks Cowboys NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 28 Sharks OR Cowboys`

## Loops

- **Research refine**: not needed (gate passed: True, 20 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - Market price $1.44 is not sourced from research.
    - Math drivers '5-game form: possession pct', 'Away travel to venue', '5-game form: penalties conceded', and 'Away rest' were omitted from the evaluation.
    - recalibrated: home 0.72 → home 0.72

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | fail | The 'market price of $1.44' is not mentioned in any research body_excerpt or scene field. |
| `availability_direction` | pass | Claims that Hynes, Trindall, and others are returning match the sharks.com.au source. |
| `shap_attribution` | pass | Bradley-Terry strength and ladder points differential are correctly attributed to the Sharks' home win group. |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factor 2 is sourced from sharks.com.au. |
| `confidence_justified` | pass | Confidence of 0.72 is within 0.50-0.85 and accounts for the Sharks' poor recent form. |
| `driver_proportionality` | pass | No minor SHAP factors are treated as decisive. |
| `omitted_math_signals` | fail | Top drivers '5-game form: possession pct' (Sharks), 'Away travel to venue', '5-game form: penalties conceded', and 'Away rest' (Cowboys) were not addressed. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.