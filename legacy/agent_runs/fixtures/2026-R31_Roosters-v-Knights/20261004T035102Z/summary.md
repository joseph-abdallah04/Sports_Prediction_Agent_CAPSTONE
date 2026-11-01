# Roosters v Knights

- **Run**: `20261004T035102Z-ee5623f9`
- **When**: 2026-10-04T03:51:02.344232+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-10-04T19:30:00+11:00 at Accor Stadium (round 31)

## Verdict

**Roosters** to win, confidence 70%.

> The Roosters remain strong favorites based on a dominant ratings advantage and superior points differential. While the model notes minor factors favoring the Knights, such as travel and recent error rates, these are negligible in weight and the error driver is explicitly conflicted. The Roosters' statistical edge in strength and form outweighs the Knights' fairytale momentum.

### Key factors

- **math** — The model is heavily weighted toward the Roosters, led by Bradley-Terry strength (0.180 contribution) and ladder points differential (0.137 contribution). Factors favoring the Knights, such as '3-game form: errors' and 'Away travel to venue', provide minimal contribution (3% each), with the error driver being a conflicted value that rawly favors the home side.
- **scene** — Official standings confirm the Roosters' superiority, sitting three places higher with a significantly stronger points difference per game (+4.92 vs +1.75).
- **research** — Zero Tackle identifies the Roosters as 'red-hot favourites' against a Knights side that has relied on three consecutive upsets to reach the Grand Final.

## What the maths said

- Prediction: **Home Win**
- P(Roosters win) = **0.7064**

| Favouring Roosters (home) | Favouring Knights (away) |
| --- | --- |
| Bradley-Terry strength advantage (+0.56 log-strength) — contribution 0.180 (21% of total) | 3-game form: errors (-2.67) — contribution 0.029 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Ladder points differential per game (+3.7 points) — contribution 0.137 (16% of total) | Away travel to venue (120 km) — contribution 0.027 (3% of total) |
| Pythagorean form (last 10) (+13% expected-win gap) — contribution 0.091 (11% of total) | 5-game form: post contact metres (+78.20) — contribution 0.015 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Elo rating advantage (+60 points) — contribution 0.059 (7% of total) | 5-game workload: top3 tackle share (+0.02) — contribution 0.015 (2% of total) |
| 5-game form: effective tackle pct (+2.72) — contribution 0.031 (4% of total) | 5-game form: possession pct (-0.20) — contribution 0.014 (2% of total) |

- Attribution balance: leans **home** (home 0.693, away 0.1639)
- Value/contribution conflicts:
  - 3-game form: errors (-2.67)
  - 5-game form: post contact metres (+78.20)

## Ladder standings

As at round 31 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=31)).

- **Roosters** — 4th · 16-0-8 · PD +118 (+4.92/g)
- **Knights** — 7th · 14-0-10 · PD +42 (+1.75/g)

- Higher on ladder: **Roosters**
- Points-difference favours: **Roosters** (home−away PD/game gap: 3.17)

## What the research found

21 items kept (dropped: stale 60, wrong_round 1, noise 14, irrelevant 15, duplicate_url 1, no_body 3).

- [NRL Casualty Ward: Watson out of GF; Promising signs for Cleary](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-10-04T01:50:17+00:00
- [Team Lists NRL State Championship Team Lists: Panthers v Dolphins](https://www.nrl.com/news/2026/09/29/nrl-state-championship-team-lists/)  
  `nrl_news` 2026-10-04T01:21:30+00:00
- [Finals DCE eyeing slice of history in fairytale finale](https://www.nrl.com/news/2026/10/04/dce-eyeing-slice-of-history-in-fairytale-finale/)  
  `nrl_news` 2026-10-03T19:01:22+00:00
- [Match Preview Roosters v Knights: Watson ruled out; Graham rises for Phoenix](https://www.nrl.com/news/2026/09/29/roosters-v-knights-watson-races-clock-graham-set-to-step-up/)  
  `nrl_news` 2026-10-03T09:45:15+00:00
- [Team Lists NRL Late Mail: Grand Final - Ioelu in for Watson; Graham steps up](https://www.nrl.com/news/2026/10/01/nrl-late-mail-grand-final---roosters-sweat-on-connor/)  
  `nrl_news` 2026-10-03T09:40:06+00:00
- [World Cup Kiwis switch paves way for Gagai-Mitchell World Cup re-match](https://www.nrl.com/news/2026/10/03/kiwis-switch-paves-way-for-gagai-mitchell-world-cup-re-match/)  
  `nrl_news` 2026-10-03T02:01:17+00:00
- [Finals Mates to rivals: Coaches put friendship aside in battle for glory](https://www.nrl.com/news/2026/10/03/from-mates-to-rivals-robbo-and-holbrook-put-friendship-aside-in-battle-for-glory/)  
  `nrl_news` 2026-10-02T20:01:21+00:00
- [Team Lists NRL Team Lists: Grand Final](https://www.nrl.com/news/2026/09/29/nrl-team-lists-grand-final/)  
  `nrl_news` 2026-09-29T10:04:10+00:00
- [Team Lists NRL Late Mail: Preliminary Finals - Cogger starts, Cleary benched](https://www.nrl.com/news/2026/09/24/nrl-late-mail-preliminary-finals---walker-100-per-cent-for-return/)  
  `nrl_news` 2026-09-27T05:42:11+00:00
- [24 Hour Team List | Grand Final v Knights - Sydney Roosters](https://www.roosters.com.au/news/2026/10/03/nrl-team-list--grand-final-v-knights/)  
  `google_news_rss` 2026-10-03T09:30:00+00:00
- [Best NRL Grand Final 2026 Betting Sites, Odds and Tips for Sydney Roosters vs Newcastle Knights - Bookies.com](https://bookies.com/au/news/nrl-grand-final-betting-odds-sites-tips-2026-sydney-roosters-vs-newcastle-knights-tomorrow)  
  `google_news_rss` 2026-10-03T07:20:14+00:00
- [Sydney Roosters vs Newcastle Knights: NRL Grand Final preview and prediction - Zero Tackle](https://www.zerotackle.com/sydney-roosters-vs-newcastle-knights-nrl-grand-final-preview-and-prediction-238660/)  
  `google_news_rss` 2026-10-04T03:22:30+00:00
- [NRL Grand Final ultimate guide: Start time and everything else you need to know - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-grand-final-2026-start-time-kickoff-and-full-schedule-for-sydney-roosters-v-newcastle-knights-how-to-watch-entertainment-betting-odds/news-story/a2d4c96da83c8ba112f95afaa1b5a786)  
  `google_news_rss` 2026-10-04T02:42:05+00:00
- [Newcastle Knights’ tale burns bright but Sydney Roosters are built just for NRL’s grand occasion | Jack Snape - The Guardian](https://www.theguardian.com/sport/blog/2026/oct/04/nrl-grand-final-2026-newcastle-knights-tale-sydney-roosters-preview)  
  `google_news_rss` 2026-10-04T02:18:35+00:00
- [Finals Jess surges to career-best try tally in a season to savour](https://www.nrl.com/news/2026/10/04/jess-surges-to-career-best-try-tally-in-a-season-to-savour/)  
  `nrl_news` 2026-10-03T21:01:21+00:00
- [How a journey deep underground set Knights on path to NRL grand final](https://www.nrl.com/news/2026/10/04/how-a-journey-deep-underground-set-knights-on-path-to-nrl-grand-final/)  
  `nrl_news` 2026-10-03T19:01:21+00:00
- [‘No stone unturned’: Star speaks after meeting with NRL seals GF heartbreak — Early Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-grand-final-early-mail-teams-ins-and-outs-will-connor-watson-play-diesel-hagan-phoenix-crossland-suspension-news-updates-reaction/news-story/bdce6d0f92e2d89ee6cfe5b93fed547b)  
  `google_news_rss` 2026-10-03T11:46:13+00:00
- [24 Hour Update | Grand Final - Newcastle Knights](https://www.newcastleknights.com.au/news/2026/09/29/nrl-team-list--grand-final/)  
  `google_news_rss` 2026-10-03T09:31:22+00:00
- [Roosters vs Knights Prediction & NRL Grand Final 2026 Betting Preview - Betfred Insights](https://insights.betfred.com/rugby-league/roosters-vs-knights-prediction-betting-tips-sunday-4-october-2026/)  
  `google_news_rss` 2026-10-03T06:00:24+00:00
- [Finals The little voice on her shoulder keeps Rima going in tough times](https://www.nrl.com/news/2026/10/03/the-little-voice-on-her-shoulder-keeps-rima-going-in-tough-times/)  
  `nrl_news` 2026-10-02T23:01:22+00:00
- [NRL 2026 grand final: where the Sydney Roosters v Newcastle Knights decider will be won and lost | Angus Fontaine - The Guardian](https://www.theguardian.com/sport/blog/2026/oct/02/nrl-2026-grand-final-sydney-roosters-vs-newcastle-knights-decider-won-lost)  
  `google_news_rss` 2026-10-02T06:15:00+00:00

## Queries the agent wrote

- `Roosters NRL injury OR "late mail" OR "team list" round 31`
- `Knights NRL injury OR "late mail" OR "team list" round 31`
- `Roosters vs Knights NRL round 31 preview`
- `Roosters Knights NRL odds OR price OR favourite`
- `Roosters Knights NRL finals race OR ladder stakes`
- `Roosters Knights NRL`
- `Roosters NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Knights NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Roosters Knights NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 31 Roosters OR Knights`

## Loops

- **Research refine**: not needed (gate passed: True, 21 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The top math drivers favouring the Knights ('3-game form: errors' and 'Away travel to venue') were omitted from the evaluation.
    - recalibrated: home 0.7 → home 0.7

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | Claims regarding 'red-hot favourites' (Zero Tackle), 'seventh place' (Match Preview), and ladder positions/points diff (Scene) are all present in sources. |
| `availability_direction` | pass | No specific player availability claims were made in the judgement. |
| `shap_attribution` | pass | Bradley-Terry strength and Ladder points differential are correctly attributed to the Roosters. |
| `weather_not_headline` | pass | Weather is not mentioned in the judgement. |
| `research_used` | pass | Key factor 3 is sourced from Zero Tackle. |
| `confidence_justified` | pass | Confidence of 0.7 is within the 0.50-0.85 range and justified by ratings and differential. |
| `driver_proportionality` | pass | No minor SHAP factors were treated as decisive. |
| `omitted_math_signals` | fail | Top Knights drivers '3-game form: errors' and 'Away travel to venue (120 km)' are not addressed in the judgement. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.