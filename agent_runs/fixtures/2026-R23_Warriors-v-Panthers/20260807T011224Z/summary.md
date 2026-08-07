# Warriors v Panthers

- **Run**: `20260807T011224Z-bf2eb8b8`
- **When**: 2026-08-07T01:12:24.976741+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-07T18:00:00+10:00 at Go Media Stadium (round 23)

## Verdict

**Panthers** to win, confidence 60%.

> The Panthers are the market favorites and ladder leaders with a significant Elo and Bradley-Terry strength advantage. While the Warriors show strong recent form in run metres (+153.40) and forced drop outs, these are outweighed by Penrith's overall quality metrics and an attribution balance that leans heavily toward the away side.

### Key factors

- **math** — The Panthers hold a strong Elo rating advantage (-80 points) and Bradley-Terry strength edge, which are the primary drivers for the away win.
- **math** — Warriors show positive recent form in all run metres (+153.40 contribution 0.118) and forced drop outs (contribution 0.045), though these are offset by the Panthers' overall ratings.
- **math** — The penalty cluster rate is netted toward the Panthers (contribution 0.075), despite a raw value conflict that would otherwise favor the home side.
- **research** — Both teams face late changes in the halves: Blaize Talagi replaces Jack Cogger for Penrith, and Luke Metcalf replaces Te Maire Martin for New Zealand (nrl_news).
- **scene** — The Panthers sit 1st on the ladder with a superior points difference per game (16.21) compared to the Warriors' 3rd place finish and 11.89 differential.

**Disagreement with the model:** The model probability predicts a Home Win (0.53), but I am picking Away because the attribution_balance leans strongly toward Penrith (0.59 vs 0.38) and they are the market favorites ($1.60).

## What the maths said

- Prediction: **Home Win**
- P(Warriors win) = **0.5301**

| Favouring Warriors (home) | Favouring Panthers (away) |
| --- | --- |
| 5-game form: all run metres (+153.40) — contribution 0.118 (12% of total) | Elo rating advantage (-80 points) — contribution 0.151 (15% of total) |
| 5-game form: forced drop outs (+1.60) — contribution 0.045 (5% of total) | Bradley-Terry strength advantage (-0.72 log-strength) — contribution 0.124 (13% of total) |
| Away rest (6.0 days) — contribution 0.024 (2% of total) | 5-game momentum: penalty cluster rate (-1.40) — contribution 0.075 (8% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Home travel to venue (0 km) — contribution 0.023 (2% of total) | Head-to-head record (last 5) (20% to the home side) — contribution 0.040 (4% of total) |
| 5-game form: points against (-4.40) — contribution 0.020 (2% of total) | Pythagorean form (last 10) (-2% expected-win gap) — contribution 0.035 (4% of total) |

- Attribution balance: leans **away** (home 0.3842, away 0.5929)
- Value/contribution conflicts:
  - 5-game momentum: penalty cluster rate (-1.40)

## Ladder standings

As at round 23 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=23)).

- **Warriors** — 3th · 13-0-6 · PD +226 (+11.89/g)
- **Panthers** — 1th · 15-0-4 · PD +308 (+16.21/g)

- Higher on ladder: **Panthers**
- Points-difference favours: **Panthers** (home−away PD/game gap: -4.32)

## What the research found

19 items kept (dropped: stale 41, wrong_round 2, noise 16, irrelevant 10, duplicate_url 2, no_body 4).

- [NRL Late Mail: Round 23 - Tedesco out; Metcalf, Talagi step up](https://www.nrl.com/news/2026/08/05/nrl-late-mail-round-23---origin-guns-return-as-finals-loom/)  
  `nrl_news` 2026-08-06T10:10:17+00:00
- [NRL Team Lists: Round 23](https://www.nrl.com/news/2026/08/04/nrl-team-lists-round-23/)  
  `nrl_news` 2026-08-04T06:00:45+00:00
- [NRL Round 23 late mail: Luke Metcalf makes return, James Tedesco out](https://www.dailytelegraph.com.au/sport/nrl/supercoach-news/nrl-round-23-late-mail-roosters-sweat-with-james-tedesco-in-doubt-for-bulldogs-clash/news-story/ed64624c53566f667f73bb4ad248feb5)  
  `duckduckgo` 2026-08-05T01:13:13+00:00
- [New Zealand Warriors vs Penrith Panthers Tips, Odds, Teams & Predictions – NRL Round 23 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/new-zealand-warriors-vs-penrith-panthers-tips-odds-teams-predictions-nrl-round-23-2026/609765)  
  `google_news_rss` 2026-08-06T05:04:54+00:00
- [NRL Casualty Ward: Surgery for McLean; Martin, Nanai hamstrung](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-08-06T10:19:10+00:00
- [Match Preview Warriors v Panthers: Metcalf steps up; Blaize back in business](https://www.nrl.com/news/2026/08/04/warriors-v-panthers-taine-train-on-track-tago-in-for-mclean/)  
  `nrl_news` 2026-08-06T08:12:04+00:00
- [Warriors vs Panthers Preview & Betting Tips: NRL Round 23 2026 - Before You Bet](https://www.beforeyoubet.com.au/warriors-vs-panthers-preview-betting-tips-nrl-round-23-2026)  
  `google_news_rss` 2026-08-05T10:00:33+00:00
- [Warriors v Panthers: Round 23 - nrl.com](https://www.nrl.com/news/2026/08/05/warriors-v-panthers-round-23/)  
  `google_news_rss` 2026-08-05T04:03:56+00:00
- [NRL Updated Team List: Round 23 - Penrith Panthers](https://www.penrithpanthers.com.au/news/2026/08/06/nrl-updated-team-list-round-23/)  
  `google_news_rss` 2026-08-06T07:59:00+00:00
- [NRL 2026 team lists: Every club's confirmed lineup for Round 23 - sportingnews.com](https://www.sportingnews.com/au/rugby-league/news/nrl-team-lists-round-23-2026-lineups-injuries-results/b358f066284f90e03d93a242)  
  `google_news_rss` 2026-08-05T18:40:23+00:00
- [NRL Team List: Round 23 - Penrith Panthers](https://www.penrithpanthers.com.au/news/2026/08/04/nrl-team-list-round-23/)  
  `google_news_rss` 2026-08-04T05:59:00+00:00
- [NRL Round 23 late mail: Luke Metcalf makes stunning return, Roosters sweat on James Tedesco](https://www.goldcoastbulletin.com.au/sport/nrl/supercoach-news/nrl-round-23-late-mail-roosters-sweat-with-james-tedesco-in-doubt-for-bulldogs-clash/news-story/ed64624c53566f667f73bb4ad248feb5)  
  `duckduckgo` 2026-08-02T01:13:13+00:00
- [Late Mail: Shock Panther recalled as exiled Warrior makes return - codesports.com.au](https://www.codesports.com.au/nrl/supercoach-news/nrl-round-23-late-mail-roosters-sweat-with-james-tedesco-in-doubt-for-bulldogs-clash/news-story/ed64624c53566f667f73bb4ad248feb5)  
  `google_news_rss` 2026-08-06T09:16:17+00:00
- [Warriors v Panthers: When they play, kick-off time, team list, injuries, NRL ladder - what to know - rnz.co.nz](https://www.rnz.co.nz/news/sport/901238/warriors-v-panthers-when-they-play-kick-off-time-team-list-injuries-nrl-ladder-what-to-know)  
  `google_news_rss` 2026-08-05T20:21:52+00:00
- [NRL Team List: Same lineup named to take on Penrith - Warriors](https://www.warriors.kiwi/news/2026/08/04/nrl-team-list-same-starting-lineup-to-take-on-penrith/)  
  `google_news_rss` 2026-08-04T05:59:26+00:00
- [NRL.com /](https://www.nrl.com/news/author/nrl.com/)  
  `duckduckgo` 2026-08-06T22:01:00+00:00
- [The brutal pre-season reality check and ‘eye-opening’ act that transformed Warriors - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-how-andrew-webster-transformed-the-warriors-roster-luke-metcalf-new-zealand-expansion/news-story/e93b6e04b8c5d46002a727007a732f49)  
  `google_news_rss` 2026-08-06T20:06:23+00:00
- [NRL News](https://www.nrl.com/news/topic/nrl-news/)  
  `duckduckgo` 2026-08-06T06:01:00+00:00
- [2026 NRL Round 23 Predictions - Ladbrokes](https://www.ladbrokes.com.au/blog/2026/08/05/2026-nrl-round-23-predictions/)  
  `google_news_rss` 2026-08-04T23:57:46+00:00

## Queries the agent wrote

- `Warriors NRL injury OR "late mail" OR "team list" round 23`
- `Panthers NRL injury OR "late mail" OR "team list" round 23`
- `Warriors vs Panthers NRL round 23 preview`
- `Warriors Panthers NRL odds OR price OR favourite`
- `Warriors Panthers NRL finals race ladder stakes`
- `Warriors Panthers NRL`
- `Warriors NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Panthers NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Warriors Panthers NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 23 Warriors OR Panthers`

## Loops

- **Research refine**: not needed (gate passed: True, 19 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The judgement omits several top math drivers from the SHAP output: '5-game form: all run metres', '5-game form: forced drop outs', and '5-game momentum: penalty cluster rate'.
    - recalibrated: away 0.6 → away 0.6

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | Matched 'Blaize Talagi replacing Jack Cogger' and 'Luke Metcalf replacing Te Maire Martin' to nrl_news body excerpts. |
| `availability_direction` | pass | Claims correctly identify replacements for missing players as per research. |
| `shap_attribution` | pass | Elo and Bradley-Terry advantages are correctly attributed to the Panthers from the favouring_Panthers_away_win group. |
| `weather_not_headline` | pass | Weather is not mentioned as a key factor. |
| `research_used` | pass | Key factor regarding late changes in the halves identifies nrl_news. |
| `confidence_justified` | pass | Confidence of 0.6 is within range and reflects a modest edge despite model disagreement. |
| `driver_proportionality` | pass | The judge focuses on the highest contributing SHAP drivers (Elo and Bradley-Terry). |
| `omitted_math_signals` | fail | Top drivers '5-game form: all run metres', '5-game form: forced drop outs' (Warriors) and '5-game momentum: penalty cluster rate' (Panthers) were not addressed. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.