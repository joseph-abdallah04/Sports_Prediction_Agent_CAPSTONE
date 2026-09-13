# Knights v Sea Eagles

- **Run**: `20260822T011159Z-e7b3d151`
- **When**: 2026-08-22T01:11:59.658228+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-22T15:00:00+10:00 at McDonald Jones Stadium (round 25)

## Verdict

**Knights** to win, confidence 70%.

> The Knights enter this match in strong form with a three-game winning streak and a significant ladder advantage (6th vs 10th). They are backed by strong recent defensive metrics, while the Sea Eagles are struggling with a four-game losing streak and the absence of five-eighth Joey Walsh. Although the Sea Eagles welcome back Tom Trbojevic, the Knights are the market favourites and hold the statistical edge.

### Key factors

- **math** — The model's prior is driven by Pythagorean form (14% contribution) and a strong 5-game defensive record in points against (8% contribution).
- **research** — The Knights have won three consecutive games, scoring at least 30 points in each (sportsnews.com.au).
- **research** — The Knights receive a boost from the return of Bradman Best and Jacob Saifiti (newcastleknights.com.au), while the Sea Eagles are missing Joey Walsh due to a jaw fracture (seaeagles.com.au).
- **math** — The model attributes some weight to the Sea Eagles via the penalty cluster rate (8% contribution), although the raw value of this metric actually favours the Knights.

## What the maths said

- Prediction: **Home Win**
- P(Knights win) = **0.6933**

| Favouring Knights (home) | Favouring Sea Eagles (away) |
| --- | --- |
| Pythagorean form (last 10) (+29% expected-win gap) — contribution 0.136 (14% of total) | 5-game momentum: penalty cluster rate (-1.20) — contribution 0.076 (8% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Ladder points differential per game (+1.3 points) — contribution 0.089 (9% of total) | 5-game form: points for (+10.80) — contribution 0.049 (5% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| 5-game form: points against (-14.00) — contribution 0.076 (8% of total) | 3-game form: errors (-2.00) — contribution 0.022 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Elo rating advantage (+75 points) — contribution 0.070 (7% of total) | 5-game form: possession pct (+2.80) — contribution 0.018 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| 5-game form: all run metres (+87.20) — contribution 0.034 (3% of total) | 5-game form: errors (-2.00) — contribution 0.018 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |

- Attribution balance: leans **home** (home 0.7327, away 0.2705)
- Value/contribution conflicts:
  - 5-game momentum: penalty cluster rate (-1.20)
  - 5-game form: points for (+10.80)
  - 3-game form: errors (-2.00)
  - 5-game form: possession pct (+2.80)
  - 5-game form: errors (-2.00)

## Ladder standings

As at round 25 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=25)).

- **Knights** — 6th · 14-0-8 · PD +76 (+3.45/g)
- **Sea Eagles** — 10th · 9-0-12 · PD +46 (+2.19/g)

- Higher on ladder: **Knights**
- Points-difference favours: **Knights** (home−away PD/game gap: 1.26)

## What the research found

18 items kept (dropped: stale 35, wrong_round 5, noise 12, irrelevant 17, duplicate_url 1, no_body 6).

- [NRL Late Mail: Round 25 - Latrell on hold; Turbo on track](https://www.nrl.com/news/2026/08/19/nrl-late-mail-round-25---trell-touch-and-go-best-good-to-go/)  
  `nrl_news` 2026-08-21T10:04:46+00:00
- [NRL Team Lists: Round 25](https://www.nrl.com/news/2026/08/18/nrl-team-lists-round-25/)  
  `nrl_news` 2026-08-18T06:00:29+00:00
- [Team List: NRL Round 25 vs Knights - Manly Warringah Sea Eagles](https://www.seaeagles.com.au/news/2026/08/18/team-list-nrl-round-25-vs-knights/)  
  `google_news_rss` 2026-08-18T05:59:00+00:00
- [Newcastle Knights vs Manly Sea Eagles Tips, Odds, Teams & Predictions – NRL Round 25 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/newcastle-knights-vs-manly-sea-eagles-tips-odds-teams-predictions-nrl-round-25-2026/609972/amp)  
  `google_news_rss` 2026-08-20T02:58:58+00:00
- [NRL Casualty Ward: Surgery for Doueihi, Walsh; Turbo good to go](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-08-21T09:34:49+00:00
- [Knights v Sea Eagles: Best back on deck: Trbojevic returns](https://www.nrl.com/news/2026/08/18/knights-v-sea-eagles-best-back-on-deck-trbojevic-returns/)  
  `nrl_news` 2026-08-21T05:04:34+00:00
- [Team Update: NRL Round 25 vs Knights - Manly Warringah Sea Eagles](https://www.seaeagles.com.au/news/2026/08/21/team-update-nrl-round-25-vs-knights/)  
  `google_news_rss` 2026-08-21T05:01:21+00:00
- [24 Hour Update | Round 25 - Newcastle Knights](https://www.newcastleknights.com.au/news/2026/08/18/nrl-team-list--round-25/)  
  `google_news_rss` 2026-08-21T05:01:21+00:00
- [Knights vs Sea Eagles Preview & Betting Tips: NRL Round 25 2026 - Before You Bet](https://www.beforeyoubet.com.au/knights-vs-sea-eagles-preview-betting-tips-nrl-round-25-2026)  
  `google_news_rss` 2026-08-21T04:36:25+00:00
- [Knights vs Sea Eagles - Round 25, 2026 - Live Scores & Stats - Match Centre - Zero Tackle](https://www.zerotackle.com/knights-sea-eagles-round-25-2026-mc10396527-237065/)  
  `google_news_rss` 2026-08-16T20:41:23+00:00
- [NRL Round 25 team lists: Full squads + NRL Supercoach analysis - SC Playbook NRL](https://scplaybook.com.au/blog/2026/08/18/nrl-round-25-team-lists-full-squads-nrl-supercoach-analysis)  
  `google_news_rss` 2026-08-18T06:26:31+00:00
- [NRL Team List: Round 25 v Titans - sharks.com.au](https://www.sharks.com.au/news/2026/08/18/nrl-team-list-round-25-v-titans/)  
  `google_news_rss` 2026-08-18T05:58:00+00:00
- [Wests Tigers NRL Injury Report Round 25 - Wests Tigers](https://www.weststigers.com.au/news/2026/08/18/wests-tigers-nrl-injury-report-round-25/)  
  `google_news_rss` 2026-08-18T03:14:30+00:00
- [‘It’s his decision’: Wayne’s Latrell reveal; Foran’s Turbo warning shot to Knights — Late Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-round-25-latest-team-news-and-injury-updates-latrell-mitchell-clint-gutherson-tom-trbojevic/news-story/1362e2e046e9793d10ba74e544d57765)  
  `google_news_rss` 2026-08-22T00:07:31+00:00
- [NRL 2026: Confirmed lineups, results for Round 25 - sportingnews.com](https://www.sportingnews.com/au/rugby-league/news/nrl-team-lists-round-25-2026-lineups-injuries-results/6d589fc01ec29d216192b2fb)  
  `google_news_rss` 2026-08-21T10:18:00+00:00
- [Dolphins v Eels - Round 25, 2026](https://www.nrl.com/watch/matches/telstra-premiership/2026/round-25/full-match-replay-dolphins-v-eels---round-25-2026/)  
  `duckduckgo` 2026-08-21T01:13:00+00:00
- [Raiders vs Broncos Preview & Betting Tips: NRL Round 25 2026 - Before You Bet](https://www.beforeyoubet.com.au/raiders-vs-broncos-preview-betting-tips-nrl-round-25-2026)  
  `google_news_rss` 2026-08-20T06:04:37+00:00
- [2026 NRL Round 25 Predictions - Ladbrokes](https://www.ladbrokes.com.au/blog/2026/08/19/2026-nrl-round-25-predictions/)  
  `google_news_rss` 2026-08-19T05:28:23+00:00

## Queries the agent wrote

- `Knights NRL injury OR "late mail" OR "team list" round 25`
- `Sea Eagles NRL injury OR "late mail" OR "team list" round 25`
- `Knights vs Sea Eagles NRL round 25 preview`
- `Knights Sea Eagles NRL odds OR price OR favourite`
- `Knights Sea Eagles NRL finals race OR ladder stakes`
- `Knights Sea Eagles NRL`
- `Knights NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Sea Eagles NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Knights Sea Eagles NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 25 Knights OR Sea Eagles`

## Loops

- **Research refine**: not needed (gate passed: True, 18 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - Hallucinated market price of $1.46.
    - Omitted top math signals: '5-game form: points against' (Knights) and '5-game momentum: penalty cluster rate' (Sea Eagles).
    - recalibrated: home 0.7 → home 0.7

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | fail | The claim that the market price is '$1.46' does not appear in any research body_excerpt or title. |
| `availability_direction` | pass | Claims for Trbojevic (returning), Walsh (missing), and Best/Saifiti (returning) match the research excerpts. |
| `shap_attribution` | pass | Pythagorean form and ladder points differential are correctly attributed to the Knights. |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factors 2, 3, and 4 are sourced from research articles. |
| `confidence_justified` | pass | Confidence of 0.7 is within the 0.50-0.85 range and justified by the form/ladder gap. |
| `driver_proportionality` | pass | The judgement focuses on the highest contributing SHAP drivers. |
| `omitted_math_signals` | fail | Top drivers '5-game form: points against' (Knights) and '5-game momentum: penalty cluster rate' (Sea Eagles) were not addressed. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.