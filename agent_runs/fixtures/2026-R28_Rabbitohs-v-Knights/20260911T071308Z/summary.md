# Rabbitohs v Knights

- **Run**: `20260911T071308Z-eb7348f7`
- **When**: 2026-09-11T07:13:08.676919+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-09-11T19:50:00+10:00 at Allianz Stadium (round 28)

## Verdict

**Rabbitohs** to win, confidence 61%.

> The Rabbitohs are favoured by a math prior of 0.56 and market pricing of $1.40 (market_mentions). Research confirms this advantage, noting the ominous form of Latrell Mitchell and a severe injury toll for the Knights, with key players Dylan Brown, Jacob Saifiti, Dylan Lucas, and Trey Mooney all ruled out for the season. While the model nets the penalty cluster rate driver toward the Knights, the raw value of that stat actually favours the Rabbitohs.

- **Research vs math:** confirms
- **Strongest reason it could lose:** The Knights have proven they can beat the Rabbitohs this season, winning their Round 9 encounter 42-38.
- **Loss reason is specific:** True

### Key factors

- **math** — Home win probability of 0.56, supported by superior 5-game run metres and a positive ladder points differential per game.
- **research** — The Knights are missing significant talent with Dylan Brown, Jacob Saifiti, Dylan Lucas, and Trey Mooney all gone for the season, while Latrell Mitchell is returning in ominous form (nrl_news).
- **math** — The penalty cluster rate is a material driver (12% contribution), though it is a conflict where the raw value actually favours the home side.

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

18 items kept (dropped: stale 70, wrong_round 1, noise 7, irrelevant 28, duplicate_url 2, no_body 5).

- [Knights Phoenix rises as Holbrook looks to keep the dream alive](https://www.nrl.com/news/2026/09/11/phoenix-rises-as-holbrook-looks-to-keep-the-dream-alive/)  
  `nrl_news` 2026-09-10T20:01:21+00:00
- [Knights I know how Toby felt: Ponga wary of getting 'Latrell-ed'... again](https://www.nrl.com/news/2026/09/07/i-know-how-toby-felt-ponga-wary-of-getting-latrell-ed/)  
  `nrl_news` 2026-09-07T06:14:07+00:00
- [Team Lists NRL Late Mail: Finals Week 1](https://www.nrl.com/news/2026/09/10/nrl-late-mail-finals-week-1/)  
  `nrl_news` 2026-09-11T06:08:34+00:00
- [Finals History lesson: Last time the contenders met in a final 31 mins ago](https://www.nrl.com/news/2026/09/11/history-lesson-last-time-the-contenders-met-in-a-final/)  
  `nrl_news` 2026-09-11T06:42:46+00:00
- [Finals 'No one gave us a chance': Chasing pack desperate to defy history 33 mins ago](https://www.nrl.com/news/2026/09/10/no-one-gave-us-a-chance-chasing-pack-desperate-to-defy-history/)  
  `nrl_news` 2026-09-11T06:40:01+00:00
- [Rabbitohs How Adam and Millie turned the Book of Feuds into a romance novel](https://www.nrl.com/news/2026/09/11/how-adam-and-millie-turned-the-book-of-feuds-into-a-romance-novel/)  
  `nrl_news` 2026-09-11T00:01:52+00:00
- [Finals 'Falling into place': New mindset driving Latrell's premiership charge](https://www.nrl.com/news/2026/09/11/falling-into-place-new-mindset-driving-latrells-premiership-charge/)  
  `nrl_news` 2026-09-10T20:01:22+00:00
- [Match Preview Rabbitohs v Knights: Tallis gets green light; Manuleleua's miracle](https://www.nrl.com/news/2026/09/08/rabbitohs-v-knights-tallis-gets-green-light-manuleleuas-miracle/)  
  `nrl_news` 2026-09-10T09:52:02+00:00
- [Rabbitohs Two into seven won't go but Bud and Jamie find the solution](https://www.nrl.com/news/2026/09/10/two-into-seven-wont-go-but-bud-and-jamie-find-the-solution/)  
  `nrl_news` 2026-09-09T20:01:21+00:00
- [Knights They can be my wingmen anytime: Ponga pins faith in flyers](https://www.nrl.com/news/2026/09/09/they-can-be-my-wingmen-anytime-ponga-pins-faith-in-flyers/)  
  `nrl_news` 2026-09-09T06:01:31+00:00
- [Wayne’s Latrell warning as Knights boost confirmed; Sharks stars face final hurdle — Finals Late Mail - foxsports.com.au](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-finals-2026-week-1-team-news-injuries-changes-late-mail-who-is-in-and-out/news-story/19748a07cd154a6af4a7810773fdcf09)  
  `google_news_rss` 2026-09-11T00:09:44+00:00
- [Rabbitohs vs Knights Prediction & NRL Betting Preview - 11/9/26 - Betfred Insights](https://insights.betfred.com/rugby-league/rabbitohs-vs-knights-prediction-betting-tips-friday-11-september-2026/)  
  `google_news_rss` 2026-09-11T07:09:44+00:00
- [South Sydney Rabbitohs vs Newcastle Knights: NRL elimination final preview and prediction - Zero Tackle](https://www.zerotackle.com/south-sydney-rabbitohs-vs-newcastle-knights-nrl-elimination-final-preview-and-prediction-237970/)  
  `google_news_rss` 2026-09-10T22:54:27+00:00
- [South Sydney Rabbitohs vs Newcastle Knights live stream: How to watch the NRL finals online or on TV, start time, squads - Zero Tackle](https://www.zerotackle.com/south-sydney-rabbitohs-vs-newcastle-knights-live-stream-how-to-watch-the-nrl-finals-online-or-on-tv-start-time-squads-237971/)  
  `google_news_rss` 2026-09-10T20:04:14+00:00
- [Shock Roosters comeback in mass changes; Wayne’s big switch as stars return: Teams Analysis - foxsports.com.au](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-week-one-finals-team-lists-selection-news-and-injuries-jackson-ford-and-braydon-trindall-return-from-injuries/news-story/0c9c8d769df7b6c49596fabb0090a2ac)  
  `google_news_rss` 2026-09-10T10:58:06+00:00
- [24 Hour Update | Elimination Final - Newcastle Knights](https://www.newcastleknights.com.au/news/2026/09/08/nrl-team-list--elimination-final/)  
  `google_news_rss` 2026-09-10T09:50:51+00:00
- [Rabbitohs vs Knights Preview & Betting Tips: 2026 NRL Elimination Final - Before You Bet](https://www.beforeyoubet.com.au/rabbitohs-vs-knights-preview-betting-tips-2026-nrl-elimination-final)  
  `google_news_rss` 2026-09-10T06:04:14+00:00
- [Rabbitohs v Knights: Finals Week 1 - NRL.com](https://www.nrl.com/news/2026/09/09/rabbitohs-v-knights-finals-week-1/)  
  `google_news_rss` 2026-09-09T06:10:58+00:00

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

- **Research refine**: not needed (gate passed: True, 18 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The market price '$1.40' is not sourced from the research provided.
    - The material SHAP driver '5-game momentum: penalty cluster rate' is omitted from the evaluation.
    - recalibrated: home 0.61 → home 0.61

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | fail | The market price '$1.40' does not appear in any research body_excerpt or price_quote; the only price mentioned is '21/10' for a 1-12 win. |
| `availability_direction` | pass | Claims regarding Latrell Mitchell's form and the Knights' injury list match the research excerpts. |
| `shap_attribution` | pass | Run metres and ladder differential are correctly attributed to the Rabbitohs (home_win group). |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factor 2 is sourced from nrl_news regarding injuries and Latrell Mitchell. |
| `confidence_justified` | pass | Confidence increase from 0.56 to 0.61 is justified by specific availability news (4 key Knights players out) and Latrell Mitchell's form. |
| `driver_proportionality` | pass | No minor SHAP factors are treated as decisive. |
| `omitted_math_signals` | fail | Material driver '5-game momentum: penalty cluster rate (-1.00)' (12% of total) is not mentioned or evaluated in the judgement. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.