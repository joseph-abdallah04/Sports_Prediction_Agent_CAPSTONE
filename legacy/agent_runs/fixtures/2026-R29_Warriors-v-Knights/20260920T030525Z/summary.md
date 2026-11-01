# Warriors v Knights

- **Run**: `20260920T030525Z-4afff3c9`
- **When**: 2026-09-20T03:05:25.417651+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-09-20T16:05:00+10:00 at Eden Park (round 29)

## Verdict

**Warriors** to win, confidence 72%.

> The Warriors are strong favourites at Eden Park, supported by a significant Elo and strength advantage and a dominant regular-season record (2nd vs 7th). While the Knights have minor edges in recent line-break form and travel metrics, the Warriors' recent possession dominance (+6.00 over 5 games) and the return of Leka Halasima outweigh these factors. The market also aligns with this view, pricing the Warriors as clear favourites ($1.48).

### Key factors

- **math** — The model shows a strong home edge driven by a +95 point Elo rating advantage, a +0.52 Bradley-Terry strength advantage, and a significant 5-game possession percentage advantage (+6.00).
- **scene** — The Warriors finished the regular season significantly higher on the ladder (Position 2) with a points differential of +310 compared to the Knights' +42.
- **research** — The Warriors receive a boost with star player Leka Halasima returning to the interchange for this match ('NRL Late Mail: Finals Week 2').

## What the maths said

- Prediction: **Home Win**
- P(Warriors win) = **0.7520**

| Favouring Warriors (home) | Favouring Knights (away) |
| --- | --- |
| Bradley-Terry strength advantage (+0.52 log-strength) — contribution 0.178 (12% of total) | ctx travel km home (no data) — contribution 0.037 (3% of total) |
| 5-game form: possession pct (+6.00) — contribution 0.162 (11% of total) | 3-game form: possession pct (+8.33) — contribution 0.029 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Ladder points differential per game (+9.9 points) — contribution 0.160 (11% of total) | 5-game form: line breaks (-2.40) — contribution 0.025 (2% of total) |
| Elo rating advantage (+95 points) — contribution 0.142 (10% of total) | 5-game form: penalties conceded (-1.40) — contribution 0.025 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Pythagorean form (last 10) (+27% expected-win gap) — contribution 0.102 (7% of total) | 5-game form: errors (-2.00) — contribution 0.024 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |

- Attribution balance: leans **home** (home 1.0938, away 0.3434)
- Value/contribution conflicts:
  - 3-game form: possession pct (+8.33)
  - 5-game form: penalties conceded (-1.40)
  - 5-game form: errors (-2.00)

## Ladder standings

As at round 29 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=29)).

- **Warriors** — 2th · 18-0-6 · PD +310 (+12.92/g)
- **Knights** — 7th · 14-0-10 · PD +42 (+1.75/g)

- Higher on ladder: **Warriors**
- Points-difference favours: **Warriors** (home−away PD/game gap: 11.17)

## What the research found

20 items kept (dropped: stale 67, noise 12, irrelevant 17, duplicate_url 2, no_body 3).

- [Finals 'Big-game player': The spark igniting Ponga's finals charge](https://www.nrl.com/news/2026/09/18/big-game-player-the-spark-igniting-pongas-finals-charge/)  
  `nrl_news` 2026-09-18T06:01:21+00:00
- [NRL Casualty Ward: Sharks lose Hynes, Hiroti; Lucas returns](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-09-19T12:43:48+00:00
- [NRL Late Mail: Finals Week 2 - Miracle man Lucas; Leka returns](https://www.nrl.com/news/2026/09/17/nrl-late-mail-finals-week-2---lucas-in-the-mix/)  
  `nrl_news` 2026-09-19T08:26:12+00:00
- [Match Preview Warriors v Knights: Halasima good to go; Lucas completes miracle](https://www.nrl.com/news/2026/09/15/warriors-v-knights-leka-dwz-in-mix-lucas-nears-return/)  
  `nrl_news` 2026-09-19T06:15:46+00:00
- [NRL Team Lists: Finals Week 2](https://www.nrl.com/news/2026/09/15/nrl-team-lists-finals-week-2/)  
  `nrl_news` 2026-09-15T05:59:00+00:00
- [NRL Late Mail: Finals Week 1 - Talagi's new role; Crichton ruled out](https://www.nrl.com/news/2026/09/10/nrl-late-mail-finals-week-1/)  
  `nrl_news` 2026-09-13T04:42:43+00:00
- [NRL injury record looms as Knights recall Origin forward for Warriors final - Yahoo News Australia](https://au.news.yahoo.com/nrl-injury-record-looms-knights-061642409.html)  
  `google_news_rss` 2026-09-19T06:16:42+00:00
- [Knight’s incredible comeback from horror injury; Roosters take aim at Sharks star — NRL Daily - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-fletcher-sharpes-incredible-comeback-from-injury-roosters-to-make-life-hell-for-braydon-trindall-inside-the-brilliance-of-mark-nawaqanitawase-nrl-daily-nrl-news/news-story/8169442eb6c64651fffbb6705bc9c2e1)  
  `google_news_rss` 2026-09-18T23:06:53+00:00
- [Warriors confirm Ford injury status, reveal Metcalf, Berry update - Zero Tackle](https://www.zerotackle.com/warriors-confirm-ford-injury-status-reveal-metcalf-berry-update-238216/)  
  `google_news_rss` 2026-09-18T07:38:41+00:00
- [Warriors v Knights: Line-ups, kickoff time, how to watch – all you need to know for semi-final](https://www.nzherald.co.nz/sport/rugby-league/warriors/warriors-v-knights-line-ups-kickoff-time-how-to-watch-all-you-need-to-know-for-semi-final/UT5SCBGKGND7NLEWEPJH4A3ORE/)  
  `duckduckgo` 2026-09-18T03:06:29+00:00
- [Preview: Can the Warriors prevail in must-win joust against Knights? - 1News](https://www.1news.co.nz/2026/09/18/preview-can-the-warriors-prevail-in-must-win-joust-against-knights/)  
  `google_news_rss` 2026-09-18T01:43:36+00:00
- ['Just be excited': Warriors v Knights – all you need to know for NRL semi-final](https://www.newstalkzb.co.nz/news/sport/warriors-v-knights-line-ups-kickoff-time-how-to-watch-all-you-need-to-know-for-semi-final/)  
  `duckduckgo` 2026-09-17T03:06:26+00:00
- [New Zealand Warriors vs Newcastle Knights Tips, Odds, Teams & Predictions – NRL Finals Week 2 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/new-zealand-warriors-vs-newcastle-knights-tips-odds-teams-predictions-nrl-finals-week-2-2026/610317)  
  `google_news_rss` 2026-09-17T02:49:19+00:00
- [The 'forgotten' match: Why Eden Park boss was wrong about NZ's biggest league occasion - NZ Herald](https://www.nzherald.co.nz/sport/rugby-league/warriors-vs-knights-why-nrl-finals-match-at-eden-park-raises-conflicting-emotions-for-fans/premium/QUBNNX7APRFEXNQX6IEQHZQOVU/)  
  `google_news_rss` 2026-09-19T23:12:47+00:00
- [Warriors vs Knights Prediction & NRL Betting Preview - 20/9/26 - Betfred Insights](https://insights.betfred.com/rugby-league/warriors-vs-knights-prediction-betting-tips-sunday-20-september-2026/)  
  `google_news_rss` 2026-09-19T20:04:44+00:00
- [Finals Immortal advice: How Johns helped Knights unlock attacking mindset](https://www.nrl.com/news/2026/09/20/immortal-advice-how-johns-helped-knights-unlock-attacking-mindset/)  
  `nrl_news` 2026-09-19T20:01:21+00:00
- [New Zealand Warriors v Newcastle Knights - Finals week 2, 2026 - NRL Score Centre - Live NRL Scores - ABC News & Headlines – Australian Broadcasting Corporation](https://www.abc.net.au/news/sport/score-centre/nrl/2026-09-20/warriors-knights/231203314)  
  `google_news_rss` 2026-09-19T12:40:32+00:00
- [Warriors vs Knights Preview & Betting Tips: 2026 NRL Semi Final - Before You Bet](https://www.beforeyoubet.com.au/warriors-vs-knights-preview-betting-tips-2026-nrl-semi-final)  
  `google_news_rss` 2026-09-19T11:29:20+00:00
- [Knights Lucas races clock as Saturday deadline looms for comeback call](https://www.nrl.com/news/2026/09/18/lucas-races-clock-as-saturday-deadline-looms-for-comeback-call/)  
  `nrl_news` 2026-09-18T01:01:20+00:00
- [Warriors 'Test footy vibes': JFH embraces Eden Park magic](https://www.nrl.com/news/2026/09/18/test-footy-vibes-jfh-embraces-eden-park-magic/)  
  `nrl_news` 2026-09-17T22:01:21+00:00

## Queries the agent wrote

- `Warriors NRL injury OR "late mail" OR "team list" round 29`
- `Knights NRL injury OR "late mail" OR "team list" round 29`
- `Warriors vs Knights NRL round 29 preview`
- `Warriors Knights NRL odds OR price OR favourite`
- `Warriors Knights NRL finals race OR ladder stakes`
- `Warriors Knights NRL`
- `Warriors NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Knights NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Warriors Knights NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 29 Warriors OR Knights`

## Loops

- **Research refine**: not needed (gate passed: True, 20 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The judgement omitted several top SHAP drivers from both the home and away groups, including possession percentages, travel, and line breaks.
    - recalibrated: home 0.72 → home 0.72

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | All claims (Halasima return, Lucas return, Ponga form, ladder/PD, Dolphins loss) are matched to research bodies or scene data. |
| `availability_direction` | pass | Halasima and Lucas are correctly described as returning based on 'added to the interchange' and 'promoted into the 19-man squad'. |
| `shap_attribution` | pass | Elo and Bradley-Terry drivers are correctly attributed to the Warriors from the 'favouring_Warriors_home_win' group. |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factor 3 is sourced from 'NRL Late Mail: Finals Week 2'. |
| `confidence_justified` | pass | Confidence of 0.72 is within the 0.50-0.85 range and justified by ladder/Elo advantages. |
| `driver_proportionality` | pass | The judgement focuses on the highest-weight drivers (Elo, Bradley-Terry) and does not overstate minor factors. |
| `omitted_math_signals` | fail | Top drivers '5-game form: possession pct' (Warriors), 'ctx travel km home', '3-game form: possession pct', and '5-game form: line breaks' (Knights) were not addressed. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.