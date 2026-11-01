# Roosters v Knights

- **Run**: `20261004T040114Z-a5f95e80`
- **When**: 2026-10-04T04:01:14.328669+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-10-04T19:30:00+11:00 at Accor Stadium (round 31)

## Verdict

**Roosters** to win, confidence 63%.

> The Roosters are strong mathematical favourites based on a significant Bradley-Terry strength advantage and superior ladder differential. While Zero Tackle describes them as red-hot favourites, the loss of Connor Watson to a concussion (nrl_news) creates a specific availability conflict that reduces confidence in the prior. I have adjusted the confidence downward from the math prior of 0.7064 to account for this loss.

- **Research vs math:** conflicts
- **Strongest reason it could lose:** The Roosters have lost Connor Watson to a concussion, forcing the inclusion of inexperienced youngster Benaiah Ioelu in the Grand Final side.
- **Loss reason is specific:** True

### Key factors

- **math** — Significant Bradley-Terry strength advantage (contribution 0.180) and ladder points differential per game (contribution 0.137).
- **research** — Connor Watson has been ruled out of the Grand Final due to a concussion, replaced by Benaiah Ioelu (nrl_news).
- **scene** — Roosters hold a higher ladder position (4th vs 7th) and a superior points difference per game (4.92 vs 1.75).

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

20 items kept (dropped: stale 59, wrong_round 1, noise 10, irrelevant 24, evergreen_casualty_ward 1, duplicate_url 2, no_body 3).

- [Team Lists NRL Team Lists: Grand Final](https://www.nrl.com/news/2026/09/29/nrl-team-lists-grand-final/)  
  `nrl_news` 2026-09-29T10:04:10+00:00
- [Team Lists NRL Late Mail: Grand Final - Ioelu in for Watson; Graham steps up](https://www.nrl.com/news/2026/10/01/nrl-late-mail-grand-final---roosters-sweat-on-connor/)  
  `nrl_news` 2026-10-03T09:40:06+00:00
- [Finals DCE eyeing slice of history in fairytale finale](https://www.nrl.com/news/2026/10/04/dce-eyeing-slice-of-history-in-fairytale-finale/)  
  `nrl_news` 2026-10-03T19:01:22+00:00
- [How a journey deep underground set Knights on path to NRL grand final](https://www.nrl.com/news/2026/10/04/how-a-journey-deep-underground-set-knights-on-path-to-nrl-grand-final/)  
  `nrl_news` 2026-10-03T19:01:21+00:00
- [Match Preview Roosters v Knights: Watson ruled out; Graham rises for Phoenix](https://www.nrl.com/news/2026/09/29/roosters-v-knights-watson-races-clock-graham-set-to-step-up/)  
  `nrl_news` 2026-10-03T09:45:15+00:00
- [World Cup Kiwis switch paves way for Gagai-Mitchell World Cup re-match](https://www.nrl.com/news/2026/10/03/kiwis-switch-paves-way-for-gagai-mitchell-world-cup-re-match/)  
  `nrl_news` 2026-10-03T02:01:17+00:00
- [Finals Mates to rivals: Coaches put friendship aside in battle for glory](https://www.nrl.com/news/2026/10/03/from-mates-to-rivals-robbo-and-holbrook-put-friendship-aside-in-battle-for-glory/)  
  `nrl_news` 2026-10-02T20:01:21+00:00
- [12 Knights In pictures: Knights fans get around their heroes](https://www.nrl.com/news/2026/09/30/in-pictures-newcastle-knights-fan-day/)  
  `nrl_news` 2026-09-30T05:05:46+00:00
- [Finals Knights riding wave of support as fans take over Harbour Bridge](https://www.nrl.com/news/2026/09/28/knights-riding-wave-of-support-as-fans-takeover-harbour-bridge/)  
  `nrl_news` 2026-09-28T08:45:09+00:00
- [24 Hour Team List | Grand Final v Knights - Sydney Roosters](https://www.roosters.com.au/news/2026/10/03/nrl-team-list--grand-final-v-knights/)  
  `google_news_rss` 2026-10-03T09:30:00+00:00
- [Best NRL Grand Final 2026 Betting Sites, Odds and Tips for Sydney Roosters vs Newcastle Knights - Bookies.com](https://bookies.com/au/news/nrl-grand-final-betting-odds-sites-tips-2026-sydney-roosters-vs-newcastle-knights-tomorrow)  
  `google_news_rss` 2026-10-03T07:20:14+00:00
- [Sydney Roosters vs Newcastle Knights: NRL Grand Final preview and prediction - Zero Tackle](https://www.zerotackle.com/sydney-roosters-vs-newcastle-knights-nrl-grand-final-preview-and-prediction-238660/)  
  `google_news_rss` 2026-10-04T03:22:30+00:00
- [Newcastle Knights’ tale burns bright but Sydney Roosters are built just for NRL’s grand occasion | Jack Snape - The Guardian](https://www.theguardian.com/sport/blog/2026/oct/04/nrl-grand-final-2026-newcastle-knights-tale-sydney-roosters-preview)  
  `google_news_rss` 2026-10-04T03:17:34+00:00
- [NRL Grand Final ultimate guide: Start time and everything else you need to know - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-grand-final-2026-start-time-kickoff-and-full-schedule-for-sydney-roosters-v-newcastle-knights-how-to-watch-entertainment-betting-odds/news-story/a2d4c96da83c8ba112f95afaa1b5a786)  
  `google_news_rss` 2026-10-04T02:42:05+00:00
- [‘No stone unturned’: Star speaks after meeting with NRL seals GF heartbreak — Early Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-grand-final-early-mail-teams-ins-and-outs-will-connor-watson-play-diesel-hagan-phoenix-crossland-suspension-news-updates-reaction/news-story/bdce6d0f92e2d89ee6cfe5b93fed547b)  
  `google_news_rss` 2026-10-03T11:46:13+00:00
- [24 Hour Update | Grand Final - Newcastle Knights](https://www.newcastleknights.com.au/news/2026/09/29/nrl-team-list--grand-final/)  
  `google_news_rss` 2026-10-03T09:31:22+00:00
- [Roosters vs Knights Prediction & NRL Grand Final 2026 Betting Preview - Betfred Insights](https://insights.betfred.com/rugby-league/roosters-vs-knights-prediction-betting-tips-sunday-4-october-2026/)  
  `google_news_rss` 2026-10-03T06:00:24+00:00
- [NRL 2026 grand final: where the Sydney Roosters v Newcastle Knights decider will be won and lost | Angus Fontaine - The Guardian](https://www.theguardian.com/sport/blog/2026/oct/02/nrl-2026-grand-final-sydney-roosters-vs-newcastle-knights-decider-won-lost)  
  `google_news_rss` 2026-10-02T06:15:00+00:00
- [2026 NRL Grand Final: Roosters vs Knights Preview & Betting Tips - Before You Bet](https://www.beforeyoubet.com.au/2026-nrl-grand-final-roosters-vs-knights-preview-betting-tips)  
  `google_news_rss` 2026-10-01T04:19:14+00:00
- ['It's amazing': Newcastle Knights legend speaks ahead of NRL grand final](https://www.newstalkzb.co.nz/on-air/weekend-sport-with-jason-pine/audio/robbie-odavis-former-newcastle-knights-star-speaks-ahead-of-nrl-grand-final/)  
  `duckduckgo` 2026-10-01T04:02:10+00:00

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

- **Research refine**: not needed (gate passed: True, 20 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - Material SHAP driver 'Pythagorean form (last 10)' is omitted from the evaluation.
    - no recalibration needed, so the judgement stands as first written

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | Claims regarding Connor Watson/Benaiah Ioelu are in nrl_news; 'red-hot favourites' is in Zero Tackle; ladder/points data is in set_fixture_scene. |
| `availability_direction` | pass | Judgement correctly identifies Connor Watson as ruled out per the research. |
| `shap_attribution` | pass | Bradley-Terry and ladder differential are correctly attributed to the Roosters (home). |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factor 2 is sourced from nrl_news regarding Connor Watson. |
| `confidence_justified` | pass | Confidence was adjusted downward from 0.7064 to 0.63 due to a specific research conflict (injury). |
| `driver_proportionality` | pass | The most significant SHAP drivers are the ones highlighted. |
| `omitted_math_signals` | fail | Material driver 'Pythagorean form (last 10)' (11% of total) is not addressed in the summary or key factors. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.