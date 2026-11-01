# Warriors v Knights

- **Run**: `20260920T031808Z-247b2370`
- **When**: 2026-09-20T03:18:08.250589+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-09-20T16:05:00+10:00 at Eden Park (round 29)

## Verdict

**Warriors** to win, confidence 62%.

> The Warriors are strong mathematical favourites (0.752) supported by a significant ladder advantage and superior possession stats. Confidence is adjusted to a modest edge (0.62) because research is mixed: the Knights receive a major boost with the return of Dylan Lucas, and the Warriors are regrouping after a loss to the Dolphins, despite also welcoming back Leka Halasima.

- **Research vs math:** mixed
- **Strongest reason it could lose:** The Knights receive a significant boost with the 'miracle' return of back-rower Dylan Lucas from a fractured ankle.
- **Loss reason is specific:** True

### Key factors

- **math** — Strong Bradley-Terry strength advantage and Elo rating advantage favouring the Warriors.
- **math** — Significant 5-game form advantage in possession percentage (contribution 0.162).
- **research** — The Knights receive a 'massive boost' with the return of Dylan Lucas from a fractured ankle (NRL Late Mail).
- **research** — The Warriors welcome back Leka Halasima to the interchange (NRL Late Mail).
- **scene** — Warriors hold a significant ladder advantage, sitting 2nd with a +310 points differential compared to the Knights in 7th.

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

22 items kept (dropped: stale 64, noise 12, irrelevant 26, evergreen_casualty_ward 1, duplicate_url 1, no_body 2).

- [NRL Team Lists: Finals Week 2](https://www.nrl.com/news/2026/09/15/nrl-team-lists-finals-week-2/)  
  `nrl_news` 2026-09-15T05:59:00+00:00
- [Finals 'Big-game player': The spark igniting Ponga's finals charge](https://www.nrl.com/news/2026/09/18/big-game-player-the-spark-igniting-pongas-finals-charge/)  
  `nrl_news` 2026-09-18T06:01:21+00:00
- [NRL Late Mail: Finals Week 2 - Miracle man Lucas; Leka returns](https://www.nrl.com/news/2026/09/17/nrl-late-mail-finals-week-2---lucas-in-the-mix/)  
  `nrl_news` 2026-09-19T08:26:12+00:00
- [Finals Immortal advice: How Johns helped Knights unlock attacking mindset](https://www.nrl.com/news/2026/09/20/immortal-advice-how-johns-helped-knights-unlock-attacking-mindset/)  
  `nrl_news` 2026-09-19T20:01:21+00:00
- [Match Preview Warriors v Knights: Halasima good to go; Lucas completes miracle](https://www.nrl.com/news/2026/09/15/warriors-v-knights-leka-dwz-in-mix-lucas-nears-return/)  
  `nrl_news` 2026-09-19T06:15:46+00:00
- [Knights Lucas races clock as Saturday deadline looms for comeback call](https://www.nrl.com/news/2026/09/18/lucas-races-clock-as-saturday-deadline-looms-for-comeback-call/)  
  `nrl_news` 2026-09-18T01:01:20+00:00
- [Finals Kirra v Jesse: You'll get a real kick out of this contest](https://www.nrl.com/news/2026/09/18/kirra-v-jesse-youll-get-a-real-kick-out-of-this-contest/)  
  `nrl_news` 2026-09-18T00:01:51+00:00
- [Warriors 'Test footy vibes': JFH embraces Eden Park magic](https://www.nrl.com/news/2026/09/18/test-footy-vibes-jfh-embraces-eden-park-magic/)  
  `nrl_news` 2026-09-17T22:01:21+00:00
- [Warriors Webster draws on Panthers lessons as Wahs take 'scenic route' to prelim](https://www.nrl.com/news/2026/09/17/webster-draws-on-panthers-lessons-as-wahs-take-scenic-route/)  
  `nrl_news` 2026-09-17T04:01:21+00:00
- [Finals Warriors to host historic final at Eden Park](https://www.nrl.com/news/2026/09/13/warriors-to-host-historic-final-at-eden-park/)  
  `nrl_news` 2026-09-12T23:28:55+00:00
- [Knights’ huge boost all but final; Roosters’ return as Sharks make switch: NRL Late Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-semifinals-latest-team-and-injury-news-warriors-provide-update-on-leka-halasima-and-dallin-watenezelezniak-dylan-lucas-comeback/news-story/7ccfbb503de78373aef9f872887c9e5a)  
  `google_news_rss` 2026-09-19T08:29:02+00:00
- [NRL injury record looms as Knights recall Origin forward for Warriors final - Yahoo News Australia](https://au.news.yahoo.com/nrl-injury-record-looms-knights-061642409.html)  
  `google_news_rss` 2026-09-19T06:16:42+00:00
- [Knight’s incredible comeback from horror injury; Roosters take aim at Sharks star — NRL Daily - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-fletcher-sharpes-incredible-comeback-from-injury-roosters-to-make-life-hell-for-braydon-trindall-inside-the-brilliance-of-mark-nawaqanitawase-nrl-daily-nrl-news/news-story/8169442eb6c64651fffbb6705bc9c2e1)  
  `google_news_rss` 2026-09-18T23:06:53+00:00
- [Warriors confirm Ford injury status, reveal Metcalf, Berry update - Zero Tackle](https://www.zerotackle.com/warriors-confirm-ford-injury-status-reveal-metcalf-berry-update-238216/)  
  `google_news_rss` 2026-09-18T07:38:41+00:00
- [Warriors v Knights: Line-ups, kickoff time, how to watch – all you need to know for semi-final](https://www.nzherald.co.nz/sport/rugby-league/warriors/warriors-v-knights-line-ups-kickoff-time-how-to-watch-all-you-need-to-know-for-semi-final/UT5SCBGKGND7NLEWEPJH4A3ORE/)  
  `duckduckgo` 2026-09-18T03:19:05+00:00
- [Preview: Can the Warriors prevail in must-win joust against Knights? - 1News](https://www.1news.co.nz/2026/09/18/preview-can-the-warriors-prevail-in-must-win-joust-against-knights/)  
  `google_news_rss` 2026-09-18T01:43:36+00:00
- ['Just be excited': Warriors v Knights – all you need to know for NRL semi-final](https://www.newstalkzb.co.nz/news/sport/warriors-v-knights-line-ups-kickoff-time-how-to-watch-all-you-need-to-know-for-semi-final/)  
  `duckduckgo` 2026-09-17T03:19:05+00:00
- [New Zealand Warriors vs Newcastle Knights Tips, Odds, Teams & Predictions – NRL Finals Week 2 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/new-zealand-warriors-vs-newcastle-knights-tips-odds-teams-predictions-nrl-finals-week-2-2026/610317)  
  `google_news_rss` 2026-09-17T02:49:19+00:00
- [The 'forgotten' match: Why Eden Park boss was wrong about NZ's biggest league occasion - NZ Herald](https://www.nzherald.co.nz/sport/rugby-league/warriors-vs-knights-why-nrl-finals-match-at-eden-park-raises-conflicting-emotions-for-fans/premium/QUBNNX7APRFEXNQX6IEQHZQOVU/)  
  `google_news_rss` 2026-09-19T23:12:47+00:00
- [Warriors vs Knights Prediction & NRL Betting Preview - 20/9/26 - Betfred Insights](https://insights.betfred.com/rugby-league/warriors-vs-knights-prediction-betting-tips-sunday-20-september-2026/)  
  `google_news_rss` 2026-09-19T20:04:44+00:00
- [New Zealand Warriors v Newcastle Knights - Finals week 2, 2026 - NRL Score Centre - Live NRL Scores - ABC News & Headlines – Australian Broadcasting Corporation](https://www.abc.net.au/news/sport/score-centre/nrl/2026-09-20/warriors-knights/231203314)  
  `google_news_rss` 2026-09-19T12:40:32+00:00
- [Warriors vs Knights Preview & Betting Tips: 2026 NRL Semi Final - Before You Bet](https://www.beforeyoubet.com.au/warriors-vs-knights-preview-betting-tips-2026-nrl-semi-final)  
  `google_news_rss` 2026-09-19T11:29:20+00:00

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

- **Research refine**: not needed (gate passed: True, 22 items with body text)
- **Verifier**: coded checklist FAILED, LLM audit FAILED
    - confidence_above_clear_edge_without_research_confirm
    - Hallucinated market price of $1.48.
    - Omitted material SHAP driver: '5-game form: possession pct'.
    - recalibrated: home 0.68 → home 0.62

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | fail | The market price '$1.48' is not mentioned in any research body_excerpt or title. |
| `availability_direction` | pass | Dylan Lucas and Leka Halasima are correctly described as returning. |
| `shap_attribution` | pass | Bradley-Terry and Elo advantages are correctly attributed to the Warriors. |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factors include Dylan Lucas and Leka Halasima sourced from NRL Late Mail. |
| `confidence_justified` | pass | Confidence was correctly adjusted downward from the 0.752 prior due to the return of Dylan Lucas and the Warriors' recent loss. |
| `driver_proportionality` | pass | The judgement focuses on the top material SHAP drivers. |
| `omitted_math_signals` | fail | Material driver '5-game form: possession pct' (11%) is not addressed in the judgement. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.