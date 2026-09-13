# Rabbitohs v Knights

- **Run**: `20260911T072556Z-65d3bde8`
- **When**: 2026-09-11T07:25:56.620692+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-09-11T19:50:00+10:00 at Allianz Stadium (round 28)

## Verdict

**Rabbitohs** to win, confidence 60%.

> The Rabbitohs hold a modest edge, supported by a strong home record and a superior points differential. While the model's attribution balance leans slightly toward the Knights, this is driven by several conflicted metrics—including penalty cluster rates and kicking metres—where the raw values actually favour the Rabbitohs. Combined with the Knights' late-season slump and Latrell Mitchell's 'ominous form', the Rabbitohs are well-positioned to win this elimination final.

### Key factors

- **math** — The Rabbitohs' strongest driver is their 5-game form in all run metres (+125.40), contributing 13% to the model's probability.
- **math** — Several key drivers favoring the Knights (penalty cluster rate, kicking metres, and errors) are marked as CONFLICT, meaning the raw statistical values actually favour the Rabbitohs.
- **research** — The Knights struggled late in the season, winning only three of their final eight games, while Latrell Mitchell is reported to be in 'ominous form' (nrl_news: 'Match Preview Rabbitohs v Knights').
- **scene** — Rabbitohs enter the match on a 2-game winning streak with a strong 9-3 home record, whereas the Knights are on a 2-game losing streak.

**Disagreement with the model:** The model's attribution balance leans away (-0.0738), but this is offset by the fact that the primary drivers for the away side are conflicted raw values that actually favour the home side.

## What the maths said

- Prediction: **Home Win**
- P(Rabbitohs win) = **0.5624**

| Favouring Rabbitohs (home) | Favouring Knights (away) |
| --- | --- |
| 5-game form: all run metres (+125.40) — contribution 0.098 (13% of total) | 5-game momentum: penalty cluster rate (-1.00) — contribution 0.094 (12% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Ladder points differential per game (+1.9 points) — contribution 0.061 (8% of total) | 5-game form: kicking metres (+136.60) — contribution 0.039 (5% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Elo rating advantage (+23 points) — contribution 0.036 (5% of total) | 3-game form: kicking metres (+292.33) — contribution 0.032 (4% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Bradley-Terry strength advantage (+0.12 log-strength) — contribution 0.026 (3% of total) | Pythagorean form (last 10) (-3% expected-win gap) — contribution 0.031 (4% of total) |
| 5-game form: points against (-3.40) — contribution 0.018 (2% of total) | 3-game form: errors (-2.33) — contribution 0.027 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |

- Attribution balance: leans **away** (home 0.3505, away 0.4243)
- Value/contribution conflicts:
  - 5-game momentum: penalty cluster rate (-1.00)
  - 5-game form: kicking metres (+136.60)
  - 3-game form: kicking metres (+292.33)
  - 3-game form: errors (-2.33)

## Ladder standings

As at round 28 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=28)).

- **Rabbitohs** — 6th · 14-0-10 · PD +113 (+4.71/g)
- **Knights** — 7th · 14-0-10 · PD +42 (+1.75/g)

- Higher on ladder: **Rabbitohs**
- Points-difference favours: **Rabbitohs** (home−away PD/game gap: 2.96)

## What the research found

20 items kept (dropped: stale 68, wrong_round 1, noise 10, irrelevant 15, duplicate_url 2, no_body 3).

- [Finals History lesson: Last time the contenders met in a final 43 mins ago](https://www.nrl.com/news/2026/09/11/history-lesson-last-time-the-contenders-met-in-a-final/)  
  `nrl_news` 2026-09-11T06:42:46+00:00
- [Finals 'No one gave us a chance': Chasing pack desperate to defy history 46 mins ago](https://www.nrl.com/news/2026/09/10/no-one-gave-us-a-chance-chasing-pack-desperate-to-defy-history/)  
  `nrl_news` 2026-09-11T06:40:01+00:00
- [Team Lists NRL Late Mail: Finals Week 1](https://www.nrl.com/news/2026/09/10/nrl-late-mail-finals-week-1/)  
  `nrl_news` 2026-09-11T06:08:34+00:00
- [Finals 'Falling into place': New mindset driving Latrell's premiership charge](https://www.nrl.com/news/2026/09/11/falling-into-place-new-mindset-driving-latrells-premiership-charge/)  
  `nrl_news` 2026-09-10T20:01:22+00:00
- [Match Preview Rabbitohs v Knights: Tallis gets green light; Manuleleua's miracle](https://www.nrl.com/news/2026/09/08/rabbitohs-v-knights-tallis-gets-green-light-manuleleuas-miracle/)  
  `nrl_news` 2026-09-10T09:52:02+00:00
- [NRL Casualty Ward: Pec pain over for Ford; Crichton good to go](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-09-08T06:08:14+00:00
- [Team Lists NRL Team Lists: Finals Week 1](https://www.nrl.com/news/2026/09/08/nrl-team-lists-finals-week-1/)  
  `nrl_news` 2026-09-08T05:59:00+00:00
- [Wayne’s Latrell warning as Knights boost confirmed; Sharks stars face final hurdle — Finals Late Mail - foxsports.com.au](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-finals-2026-week-1-team-news-injuries-changes-late-mail-who-is-in-and-out/news-story/19748a07cd154a6af4a7810773fdcf09)  
  `google_news_rss` 2026-09-11T00:09:44+00:00
- [Rabbitohs vs Knights Prediction & NRL Betting Preview - 11/9/26 - Betfred Insights](https://insights.betfred.com/rugby-league/rabbitohs-vs-knights-prediction-betting-tips-friday-11-september-2026/)  
  `google_news_rss` 2026-09-11T07:09:44+00:00
- [Match Preview Wests Tigers v Raiders: Apps, Turnbull sidelined; Dodd in for Taufa](https://www.nrl.com/news/2026/09/08/wests-tigers-v-raiders-turnbull-good-to-go-dodd-in-for-taufa/)  
  `nrl_news` 2026-09-11T06:14:16+00:00
- [Match Preview Warriors v Dolphins: Ford set to motor; Big Three return](https://www.nrl.com/news/2026/09/08/warriors-v-dolphins-ford-set-to-motor-big-three-return/)  
  `nrl_news` 2026-09-11T06:09:51+00:00
- [Rabbitohs How Adam and Millie turned the Book of Feuds into a romance novel](https://www.nrl.com/news/2026/09/11/how-adam-and-millie-turned-the-book-of-feuds-into-a-romance-novel/)  
  `nrl_news` 2026-09-11T00:01:52+00:00
- [South Sydney Rabbitohs vs Newcastle Knights: NRL elimination final preview and prediction - Zero Tackle](https://www.zerotackle.com/south-sydney-rabbitohs-vs-newcastle-knights-nrl-elimination-final-preview-and-prediction-237970/)  
  `google_news_rss` 2026-09-10T22:54:27+00:00
- [South Sydney Rabbitohs vs Newcastle Knights live stream: How to watch the NRL finals online or on TV, start time, squads - Zero Tackle](https://www.zerotackle.com/south-sydney-rabbitohs-vs-newcastle-knights-live-stream-how-to-watch-the-nrl-finals-online-or-on-tv-start-time-squads-237971/)  
  `google_news_rss` 2026-09-10T20:04:14+00:00
- [Knights Phoenix rises as Holbrook looks to keep the dream alive](https://www.nrl.com/news/2026/09/11/phoenix-rises-as-holbrook-looks-to-keep-the-dream-alive/)  
  `nrl_news` 2026-09-10T20:01:21+00:00
- [Shock Roosters comeback in mass changes; Wayne’s big switch as stars return: Teams Analysis - foxsports.com.au](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-week-one-finals-team-lists-selection-news-and-injuries-jackson-ford-and-braydon-trindall-return-from-injuries/news-story/0c9c8d769df7b6c49596fabb0090a2ac)  
  `google_news_rss` 2026-09-10T10:58:06+00:00
- [Rabbitohs vs Knights Preview & Betting Tips: 2026 NRL Elimination Final - Before You Bet](https://www.beforeyoubet.com.au/rabbitohs-vs-knights-preview-betting-tips-2026-nrl-elimination-final)  
  `google_news_rss` 2026-09-10T06:04:14+00:00
- [Rabbitohs Two into seven won't go but Bud and Jamie find the solution](https://www.nrl.com/news/2026/09/10/two-into-seven-wont-go-but-bud-and-jamie-find-the-solution/)  
  `nrl_news` 2026-09-09T20:01:21+00:00
- [Rabbitohs v Knights: Finals Week 1 - NRL.com](https://www.nrl.com/news/2026/09/09/rabbitohs-v-knights-finals-week-1/)  
  `google_news_rss` 2026-09-09T06:10:58+00:00
- [Knights They can be my wingmen anytime: Ponga pins faith in flyers](https://www.nrl.com/news/2026/09/09/they-can-be-my-wingmen-anytime-ponga-pins-faith-in-flyers/)  
  `nrl_news` 2026-09-09T06:01:31+00:00

## Queries the agent wrote

- `Rabbitohs NRL injury OR "late mail" OR "team list" round 28`
- `Knights NRL injury OR "late mail" OR "team list" round 28`
- `Rabbitohs vs Knights NRL round 28 preview`
- `Rabbitohs Knights NRL odds OR price OR favourite`
- `Rabbitohs Knights NRL finals race OR ladder stakes`
- `Rabbitohs Knights NRL`
- `Rabbitohs NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Knights NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Rabbitohs Knights NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 28 Rabbitohs OR Knights`

## Loops

- **Research refine**: not needed (gate passed: True, 20 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The judgement omitted several top SHAP drivers from both the home and away groups.
    - recalibrated: home 0.6 → home 0.6

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | All claims match research bodies (e.g., Knights winning 3 of final 8 in 'Match Preview Rabbitohs v Knights') or scene data (e.g., Rabbitohs 9-3 home record). |
| `availability_direction` | pass | Latrell Mitchell is described as fit and in-form, matching the source 'looking in ominous form'. |
| `shap_attribution` | pass | Ladder points differential and Elo rating are correctly attributed to the Rabbitohs from the 'favouring_Rabbitohs_home_win' group. |
| `weather_not_headline` | pass | Weather is not mentioned as a key factor. |
| `research_used` | pass | Key factor 2 is sourced from 'nrl_news: Match Preview Rabbitohs v Knights'. |
| `confidence_justified` | pass | Confidence of 0.6 is within the 0.50-0.85 range and justified by a 'modest edge' and home advantage. |
| `driver_proportionality` | pass | The judgement focuses on top-tier drivers and research-backed form. |
| `omitted_math_signals` | fail | Top drivers '5-game form: all run metres', '5-game momentum: penalty cluster rate', '5-game form: kicking metres', and '3-game form: kicking metres' were not addressed. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.