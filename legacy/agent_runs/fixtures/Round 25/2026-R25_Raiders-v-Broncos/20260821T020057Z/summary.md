# Raiders v Broncos

- **Run**: `20260821T020057Z-55e11046`
- **When**: 2026-08-21T02:00:57.720789+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-21T18:00:00+10:00 at GIO Stadium (round 25)

## Verdict

**Raiders** to win, confidence 72%.

> The Raiders hold a significant edge in strength and form, while the Broncos are on a four-game losing streak and missing star fullback Reece Walsh due to surgery. While the model notes minor advantages for Brisbane in head-to-head records and recent points scored, these are heavily outweighed by Canberra's overall ratings and home advantage. The match is further charged emotionally as it marks Josh Papalii's final appearance at GIO Stadium.

### Key factors

- **math** — The model identifies a strong edge for the Raiders via Bradley-Terry strength advantage (+0.32 log-strength, 14% contribution) and Elo rating (+91 points).
- **research** — The Broncos are missing star fullback Reece Walsh, who has undergone surgery to repair a syndesmosis injury (broncos.com.au).
- **research** — Raiders regain Simi Sasagi and have an emotional driver in Josh Papalii's final home game at GIO Stadium (nrl_news).
- **math** — Minor drivers favouring the Broncos, including head-to-head records and 5-game points for, provide minimal contribution (2-4% each) compared to the primary strength metrics.

## What the maths said

- Prediction: **Home Win**
- P(Raiders win) = **0.7087**

| Favouring Raiders (home) | Favouring Broncos (away) |
| --- | --- |
| Ladder points differential per game (+6.7 points) — contribution 0.154 (14% of total) | 5-game form: points for (+17.60) — contribution 0.041 (4% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Bradley-Terry strength advantage (+0.32 log-strength) — contribution 0.151 (14% of total) | Head-to-head record (last 5) (40% to the home side) — contribution 0.024 (2% of total) |
| Elo rating advantage (+91 points) — contribution 0.134 (12% of total) | 3-game form: errors (-3.00) — contribution 0.021 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Pythagorean form (last 10) (+36% expected-win gap) — contribution 0.123 (11% of total) | Away travel to venue (942 km) — contribution 0.019 (2% of total) |
| 5-game form: all run metres (+98.00) — contribution 0.042 (4% of total) | 5-game form: missed tackles (+3.80) — contribution 0.019 (2% of total) |

- Attribution balance: leans **home** (home 0.8049, away 0.2722)
- Value/contribution conflicts:
  - 5-game form: points for (+17.60)
  - 3-game form: errors (-3.00)

## Ladder standings

As at round 25 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=25)).

- **Raiders** — 12th · 10-0-12 · PD -61 (-2.77/g)
- **Broncos** — 16th · 6-0-15 · PD -198 (-9.43/g)

- Higher on ladder: **Raiders**
- Points-difference favours: **Raiders** (home−away PD/game gap: 6.66)

## What the research found

20 items kept (dropped: stale 39, wrong_round 4, noise 16, irrelevant 18, duplicate_url 2, no_body 3).

- [NRL Late Mail: Round 25 - Trell touch and go; Best good to go](https://www.nrl.com/news/2026/08/19/nrl-late-mail-round-25---trell-touch-and-go-best-good-to-go/)  
  `nrl_news` 2026-08-20T10:03:20+00:00
- [NRL Team Lists: Round 25](https://www.nrl.com/news/2026/08/18/nrl-team-lists-round-25/)  
  `nrl_news` 2026-08-18T06:00:29+00:00
- [NRL Team List Round 25 v Raiders - Brisbane Broncos](https://www.broncos.com.au/news/2026/08/18/nrl-team-list-round-25-v-raiders/)  
  `google_news_rss` 2026-08-18T05:48:55+00:00
- [Canberra Raiders vs Brisbane Broncos Tips, Odds, Teams & Predictions – NRL Round 25 2026 - sportsnews.com.au](https://www.sportsnews.com.au/nrl/canberra-raiders-vs-brisbane-broncos-tips-odds-teams-predictions-nrl-round-25-2026/609970)  
  `google_news_rss` 2026-08-20T02:52:27+00:00
- [Dolphins v Eels: Plath set to start; De Belin locked in](https://www.nrl.com/news/2026/08/18/dolphins-v-eels-plath-set-to-start-de-belin-locked-in/)  
  `nrl_news` 2026-08-20T10:03:52+00:00
- [Raiders v Broncos: Sasagi returns; Hunt set to start](https://www.nrl.com/news/2026/08/18/raiders-v-broncos-sasagi-returns-hunt-set-to-start/)  
  `nrl_news` 2026-08-20T08:03:11+00:00
- [Raiders vs Broncos Preview & Betting Tips: NRL Round 25 2026 - Before You Bet](https://www.beforeyoubet.com.au/raiders-vs-broncos-preview-betting-tips-nrl-round-25-2026)  
  `google_news_rss` 2026-08-20T06:04:37+00:00
- [NRL Casualty Ward: Mitchell eyes comeback; Surgery for Doueihi, Walsh](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-08-20T04:47:11+00:00
- [Raiders v Broncos: Round 25 - NRL.com](https://www.nrl.com/watch/news/raiders-v-broncos-round-25-1978621/)  
  `google_news_rss` 2026-08-19T05:56:26+00:00
- [Raiders v Broncos: Round 25 - NRL.com](https://www.nrl.com/news/2026/08/19/raiders-v-broncos-round-25/)  
  `google_news_rss` 2026-08-19T05:56:26+00:00
- [Raiders vs Broncos - Round 25, 2026 - Live Scores & Stats - Match Centre - Zero Tackle](https://www.zerotackle.com/raiders-broncos-round-25-2026-mc10396525-237069/)  
  `google_news_rss` 2026-08-16T19:25:22+00:00
- [NRL Team List: Round 25 v Titans - sharks.com.au](https://www.sharks.com.au/news/2026/08/18/nrl-team-list-round-25-v-titans/)  
  `google_news_rss` 2026-08-18T05:58:00+00:00
- [NRL Late Mail Round 25: Latrell Mitchell won’t play but back next week, surgery for Jock Madden](https://www.theaustralian.com.au/sport/nrl/nrl-late-mail-round-25-rabbitohs-young-gun-dayne-jennings-back-from-gruesome-injury/news-story/f9e0661b9a55ca8efcc14c9ab0b6513b)  
  `duckduckgo` 2026-08-15T02:01:48+00:00
- [Huge news on Latrell’s comeback ahead of the finals; Dragons star’s season over: Late Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-round-25-latest-team-news-and-injury-updates-latrell-mitchell-clint-gutherson-tom-trbojevic/news-story/1362e2e046e9793d10ba74e544d57765)  
  `google_news_rss` 2026-08-20T15:48:59+00:00
- [NRL Team List: Raiders v Broncos - raiders.com.au](https://www.raiders.com.au/news/2026/08/18/nrl-team-list-raiders-v-broncos/)  
  `google_news_rss` 2026-08-18T05:56:17+00:00
- [NRL News /](https://www.nrl.com/news/topic/nrl-news/)  
  `duckduckgo` 2026-08-20T20:00:00+00:00
- [Dolphins vs Eels Preview & Betting Tips: NRL Round 25 2026 - Before You Bet](https://www.beforeyoubet.com.au/dolphins-vs-eels-preview-betting-tips-nrl-round-25-2026)  
  `google_news_rss` 2026-08-20T06:04:37+00:00
- [Brandy and Jimmy's Round 25 NRL Tips - SEN](https://www.sen.com.au/news/2026/08/20/nrl-2026-brandy-and-jimmy-s-expert-round-25-tips)  
  `google_news_rss` 2026-08-20T03:05:56+00:00
- ['Carry on what he's built': Raiders' vow before Papa's swansong](https://www.nrl.com/news/2026/08/21/carry-on-what-hes-built-raiders-vow-before-papas-swansong/)  
  `nrl_news` 2026-08-20T20:01:22+00:00
- [Raiders vs Broncos Prediction & NRL Betting Preview - 21/8/26 - Betfred Insights](https://insights.betfred.com/rugby-league/raiders-vs-broncos-prediction-betting-tips-friday-21-august-2026/)  
  `google_news_rss` 2026-08-20T15:50:11+00:00

## Queries the agent wrote

- `Raiders NRL injury OR "late mail" OR "team list" round 25`
- `Broncos NRL injury OR "late mail" OR "team list" round 25`
- `Raiders vs Broncos NRL round 25 preview`
- `Raiders Broncos NRL odds OR price OR favourite`
- `Raiders Broncos NRL finals race OR ladder stakes`
- `Raiders Broncos NRL`
- `Raiders NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Broncos NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Raiders Broncos NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 25 Raiders OR Broncos`

## Loops

- **Research refine**: not needed (gate passed: True, 20 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The market price '$1.30' is a hallucination as it does not appear in the research.
    - Several top math drivers (Bradley-Terry strength, H2H record, 5-game points for) were omitted from the evaluation.
    - recalibrated: home 0.72 → home 0.72

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | fail | The market price '$1.30' is not mentioned in any research body excerpt or title. |
| `availability_direction` | pass | Reece Walsh is correctly described as missing due to surgery and Simi Sasagi as returning. |
| `shap_attribution` | pass | Ladder points differential and Elo rating are correctly attributed to the Raiders from the favouring_Raiders_home_win group. |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factors include Reece Walsh's injury and Josh Papalii's final home game from research articles. |
| `confidence_justified` | pass | Confidence of 0.72 is within the allowed range and justified by strong math signals and key injury news. |
| `driver_proportionality` | pass | The judgement focuses on the top SHAP drivers (Ladder diff, Elo) rather than minor ones. |
| `omitted_math_signals` | fail | Math drivers 'Bradley-Terry strength advantage', 'Head-to-head record (last 5)', and '5-game form: points for' are not addressed. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.