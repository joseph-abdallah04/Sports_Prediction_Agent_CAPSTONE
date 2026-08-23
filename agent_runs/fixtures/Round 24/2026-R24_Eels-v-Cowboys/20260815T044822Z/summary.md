# Eels v Cowboys

- **Run**: `20260815T044822Z-a99ec147`
- **When**: 2026-08-15T04:48:22.598240+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-15T17:30:00+10:00 at CommBank Stadium (round 24)

## Verdict

**Eels** to win, confidence 56%.

> The Eels are predicted to win based on a strong historical head-to-head record and the Cowboys' poor history at CommBank Stadium. While North Queensland is the market favourite and holds superior Elo ratings, Parramatta's recent defensive form and venue dominance provide a sufficient edge.

### Key factors

- **research** — According to 'Before You Bet', the Eels have won five of the last six meetings between these sides and the Cowboys have won only once in their last five visits to CommBank Stadium.
- **math** — The model's home-win prediction is supported by a strong head-to-head record (80% win rate) and recent defensive form, specifically the '5-game form: points against' driver (contribution 0.074).
- **math** — The model nets the '3-game form: errors' driver toward the Eels (contribution 0.053), although this is a conflicted value where the raw stat actually favours the Cowboys.
- **math** — Conversely, the Cowboys hold an advantage in '5-game form: all run metres' (contribution 0.069) and superior Elo ratings, which contributes to the model's attribution balance leaning toward the away side.
- **research** — Both teams receive availability boosts with Dylan Walker returning for the Eels and hooker Reed Mahoney returning from concussion for the Cowboys ('nrl_news').

**Disagreement with the model:** The model's attribution balance leans away (0.4673 vs 0.3849), indicating that while it predicts a home win, the aggregate weight of ratings and run-metre data favours the Cowboys.

## What the maths said

- Prediction: **Home Win**
- P(Eels win) = **0.5628**

| Favouring Eels (home) | Favouring Cowboys (away) |
| --- | --- |
| 5-game form: points against (-9.40) — contribution 0.074 (9% of total) | Elo rating advantage (-75 points) — contribution 0.133 (16% of total) |
| 3-game form: errors (+3.00) — contribution 0.053 (6% of total); CONFLICT: the raw value on its own favours the away side — the model still nets it toward home here | Bradley-Terry strength advantage (-0.45 log-strength) — contribution 0.124 (15% of total) |
| Head-to-head record (last 5) (80% to the home side) — contribution 0.044 (5% of total) | 5-game form: all run metres (-96.20) — contribution 0.069 (8% of total) |
| Ladder points differential per game (-4.5 points) — contribution 0.025 (3% of total); CONFLICT: the raw value on its own favours the away side — the model still nets it toward home here | Away rest (15.9 days) — contribution 0.027 (3% of total) |
| Home travel to venue (0 km) — contribution 0.022 (3% of total) | Away travel to venue (1,665 km) — contribution 0.021 (3% of total) |

- Attribution balance: leans **away** (home 0.3849, away 0.4673)
- Value/contribution conflicts:
  - 3-game form: errors (+3.00)
  - Ladder points differential per game (-4.5 points)

## Ladder standings

As at round 24 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=24)).

- **Eels** — 13th · 7-0-13 · PD -183 (-9.15/g)
- **Cowboys** — 8th · 12-0-9 · PD -76 (-3.62/g)

- Higher on ladder: **Cowboys**
- Points-difference favours: **Cowboys** (home−away PD/game gap: -5.53)

## What the research found

18 items kept (dropped: stale 47, wrong_round 7, noise 16, irrelevant 13, duplicate_url 3, no_body 4).

- [Team Lists NRL Late Mail: Round 24 - Crossland back, Best on hold for Knights Presented by 37 mins ago](https://www.nrl.com/news/2026/08/12/nrl-late-mail-round-24---teddy-races-clock-knights-stars-return/)  
  `nrl_news` 2026-08-15T04:11:15+00:00
- [Team Lists NRL Team Lists: Round 24](https://www.nrl.com/news/2026/08/11/nrl-team-lists-round-24/)  
  `nrl_news` 2026-08-11T05:59:00+00:00
- [Cowboys NRL team list: Round 24 v Eels - North Queensland Cowboys](https://www.cowboys.com.au/news/2026/08/11/cowboys-nrl-team-list-round-24-v-eels-reed-returns/)  
  `google_news_rss` 2026-08-11T05:53:00+00:00
- [Parramatta Eels vs North Queensland Cowboys Tips, Odds, Teams & Predictions – NRL Round 24 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/parramatta-eels-vs-north-queensland-cowboys-tips-odds-teams-predictions-nrl-round-24-2026/609874)  
  `google_news_rss` 2026-08-12T15:40:11+00:00
- [Live Blog Super Saturday: Sharks v Raiders; Eels v Cowboys; Broncos v Warriors Presented by 37 mins ago](https://www.nrl.com/news/2026/08/15/super-saturday-sharks-v-raiders-eels-v-cowboys-broncos-v-warriors/)  
  `nrl_news` 2026-08-15T04:11:51+00:00
- [Injuries NRL Casualty Ward: Fresh Reynolds injury; Ramien's season over](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-08-14T10:43:19+00:00
- [Match Preview Eels v Cowboys: Walker back on deck; Mahoney good to go](https://www.nrl.com/news/2026/08/11/eels-v-cowboys-walker-back-on-deck-mahoney-good-to-go/)  
  `nrl_news` 2026-08-14T07:37:02+00:00
- [Eels vs Cowboys Preview & Betting Tips: NRL Round 24 2026 - Before You Bet](https://www.beforeyoubet.com.au/eels-vs-cowboys-preview-betting-tips-nrl-round-24-2026)  
  `google_news_rss` 2026-08-13T07:00:00+00:00
- [NRL Press Conference: Eels v Cowboys - Round 24, 2026 - NRL.com](https://www.nrl.com/watch/matches/telstra-premiership/2026/round-24/nrl-press-conference-eels-v-cowboys---round-24-2026/)  
  `google_news_rss` 2026-08-12T09:10:00+00:00
- [Eels v Cowboys: Round 24 - NRL.com](https://www.nrl.com/watch/news/eels-v-cowboys-round-24-1975477/)  
  `google_news_rss` 2026-08-12T05:03:06+00:00
- [NRL Team List Update: Round 24 - Parramatta Eels](https://www.parraeels.com.au/news/2026/08/14/nrl-team-list-update-round-24/)  
  `google_news_rss` 2026-08-14T07:30:00+00:00
- [NRL Injury Report: Round 24 - Parramatta Eels](https://www.parraeels.com.au/news/2026/08/11/nrl-injury-report-round-24/)  
  `google_news_rss` 2026-08-11T06:00:00+00:00
- [Team List: NRL Round 24 v Dragons - Wests Tigers](https://www.weststigers.com.au/news/2026/08/11/team-list-nrl-round-24-v-dragons/)  
  `google_news_rss` 2026-08-11T06:00:00+00:00
- [NRL Team List: Round 24 - Parramatta Eels](https://www.parraeels.com.au/news/2026/08/11/nrl-team-list-round-24/)  
  `google_news_rss` 2026-08-11T06:00:00+00:00
- [NRL Late Mail: Round 24 v Raiders](https://www.sharks.com.au/news/2026/08/15/nrl-late-mail-round-24-v-raiders/)  
  `duckduckgo` 2026-08-10T04:49:00+00:00
- [Broncos vs Warriors Preview & Betting Tips: NRL Round 24 2026 - Before You Bet](https://www.beforeyoubet.com.au/broncos-vs-warriors-preview-betting-tips-nrl-round-24-2026)  
  `google_news_rss` 2026-08-15T03:17:03+00:00
- [Knights vs Titans Preview & Betting Tips: NRL Round 24 2026 - Before You Bet](https://www.beforeyoubet.com.au/knights-vs-titans-preview-betting-tips-nrl-round-24-2026)  
  `google_news_rss` 2026-08-14T14:08:33+00:00
- [NRL Round 24 teams: Raiders star axed over ‘brain explosion’ - News.com.au](https://www.news.com.au/sport/nrl/nrl-teams-round-24-eels-star-isaiah-iongi-ruled-out-for-the-season/news-story/3e8f2b9ef18a7a662bffef54b8bf3d18)  
  `google_news_rss` 2026-08-13T03:48:51+00:00

## Queries the agent wrote

- `Eels NRL injury OR "late mail" OR "team list" round 24`
- `Cowboys NRL injury OR "late mail" OR "team list" round 24`
- `Eels vs Cowboys NRL round 24 preview`
- `Eels Cowboys NRL odds OR price OR favourite`
- `Eels Cowboys NRL finals race ladder stakes form`
- `Eels Cowboys NRL`
- `Eels NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Cowboys NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Eels Cowboys NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 24 Eels OR Cowboys`

## Loops

- **Research refine**: not needed (gate passed: True, 18 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The market price '$1.52' is unsourced.
    - Math drivers '5-game form: points against', '3-game form: errors', and '5-game form: all run metres' were omitted from the evaluation.
    - recalibrated: home 0.56 → home 0.56

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | fail | The market price '$1.52' for North Queensland is not mentioned in any research body or title. |
| `availability_direction` | pass | Walker and Mahoney are correctly described as returning. |
| `shap_attribution` | pass | The head-to-head record driver is correctly attributed to the Eels (home win group). |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factors are sourced from 'Before You Bet' and 'nrl_news'. |
| `confidence_justified` | pass | Confidence (0.56) is within the allowed range and reflects the conflict between H2H history and ladder/market position. |
| `driver_proportionality` | pass | The judge acknowledges that Elo and strength ratings (larger drivers) favor the away side while using H2H to justify the pick. |
| `omitted_math_signals` | fail | Top drivers '5-game form: points against', '3-game form: errors', and '5-game form: all run metres' are not addressed. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.