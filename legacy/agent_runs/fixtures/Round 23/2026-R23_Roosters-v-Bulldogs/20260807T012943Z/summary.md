# Roosters v Bulldogs

- **Run**: `20260807T012943Z-dc44cdf6`
- **When**: 2026-08-07T01:29:43.836158+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-07T20:00:00+10:00 at Allianz Stadium (round 23)

## Verdict

**Roosters** to win, confidence 70%.

> The Roosters are strong favorites based on their second-place ladder position and a six-game winning streak. While they suffer a significant blow with captain James Tedesco sidelined (per nrl_news), their structural strength and home advantage outweigh the Bulldogs' recent surge into the top eight.

### Key factors

- **math** — The model shows a strong lean toward the home side, driven primarily by Bradley-Terry strength (0.154 contribution) and Elo rating advantage (0.152 contribution).
- **scene** — Roosters hold a significant ladder advantage (2nd vs 9th) with a points differential per game gap of +10.48.
- **research** — The Roosters are in dominant form with six consecutive wins, though they will be without James Tedesco who is ruled out until Round 24 (nrl_news).

## What the maths said

- Prediction: **Home Win**
- P(Roosters win) = **0.7404**

| Favouring Roosters (home) | Favouring Bulldogs (away) |
| --- | --- |
| Bradley-Terry strength advantage (+0.58 log-strength) — contribution 0.154 (14% of total) | 5-game form: points for (+7.80) — contribution 0.041 (4% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Elo rating advantage (+97 points) — contribution 0.152 (14% of total) | 3-game form: errors (-1.00) — contribution 0.033 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Ladder points differential per game (+10.5 points) — contribution 0.125 (11% of total) | 5-game form: penalties conceded (-0.80) — contribution 0.023 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Pythagorean form (last 10) (+13% expected-win gap) — contribution 0.107 (10% of total) | 5-game form: points against (-2.00) — contribution 0.020 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Away travel to venue (16 km) — contribution 0.063 (6% of total) | 5-game form: possession pct (+4.00) — contribution 0.018 (2% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |

- Attribution balance: leans **home** (home 0.8996, away 0.219)
- Value/contribution conflicts:
  - 5-game form: points for (+7.80)
  - 3-game form: errors (-1.00)
  - 5-game form: penalties conceded (-0.80)
  - 5-game form: points against (-2.00)
  - 5-game form: possession pct (+4.00)

## Ladder standings

As at round 23 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=23)).

- **Roosters** — 2th · 14-0-5 · PD +155 (+8.16/g)
- **Bulldogs** — 9th · 10-0-9 · PD -44 (-2.32/g)

- Higher on ladder: **Roosters**
- Points-difference favours: **Roosters** (home−away PD/game gap: 10.48)

## What the research found

18 items kept (dropped: stale 63, wrong_round 6, noise 11, irrelevant 14, duplicate_url 4, no_body 3).

- [Team Lists NRL Late Mail: Round 23 - Tedesco out; Metcalf, Talagi step up Presented by 5 mins ago](https://www.nrl.com/news/2026/08/05/nrl-late-mail-round-23---origin-guns-return-as-finals-loom/)  
  `nrl_news` 2026-08-07T01:24:43+00:00
- [Team Lists NRL Team Lists: Round 23](https://www.nrl.com/news/2026/08/04/nrl-team-lists-round-23/)  
  `nrl_news` 2026-08-04T06:00:45+00:00
- [Bulldogs Senior Pathways Team List: Round 23 - Bulldogs](https://www.bulldogs.com.au/news/2026/08/04/bulldogs-senior-pathways-team-list-round-23/)  
  `google_news_rss` 2026-08-04T06:01:25+00:00
- [NRL Casualty Ward: Surgery for McLean; Martin, Nanai hamstrung](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-08-06T10:19:10+00:00
- [Match Preview Roosters v Bulldogs: Tedesco sidelined; Tupouniua back on deck](https://www.nrl.com/news/2026/08/04/roosters-v-bulldogs-collins-returns-tupouniua-back-on-deck/)  
  `nrl_news` 2026-08-06T10:15:57+00:00
- [Roosters vs Bulldogs Preview & Betting Tips: NRL Round 23 2026 - Before You Bet](https://www.beforeyoubet.com.au/roosters-vs-bulldogs-preview-betting-tips-nrl-round-23-2026)  
  `google_news_rss` 2026-08-05T10:12:44+00:00
- [Roosters v Bulldogs: Round 23 - NRL.com](https://www.nrl.com/news/2026/08/05/roosters-v-bulldogs-round-23/)  
  `google_news_rss` 2026-08-05T04:05:52+00:00
- [NRL 24 Hour Update | Round 23 v Bulldogs - Sydney Roosters](https://www.roosters.com.au/news/2026/08/04/team-list--rd-23-v-bulldogs/)  
  `google_news_rss` 2026-08-04T06:01:24+00:00
- [Roosters vs Bulldogs - Round 23, 2026 - Live Scores & Stats - Match Centre - Zero Tackle](https://www.zerotackle.com/roosters-bulldogs-round-23-2026-mc10396508-236520/)  
  `google_news_rss` 2026-08-02T21:03:57+00:00
- [NRL Round 23 Match Preview: Gadhu Gathering](https://www.bulldogs.com.au/news/2026/08/06/nrl-round-23-match-preview-gadhu-gathering/)  
  `duckduckgo` 2026-07-29T01:30:31+00:00
- [NRL 2026 team lists: Every club's confirmed lineup for Round 23 - sportingnews.com](https://www.sportingnews.com/au/rugby-league/news/nrl-team-lists-round-23-2026-lineups-injuries-results/b358f066284f90e03d93a242)  
  `google_news_rss` 2026-08-05T18:40:23+00:00
- [NRL Team Lists Round 23: Big ins, surprise calls and every confirmed squad - Zero Tackle](https://www.zerotackle.com/round-23-team-lists-2026-236562/)  
  `google_news_rss` 2026-08-04T05:58:19+00:00
- [NRL Round 23 late mail: Luke Metcalf makes stunning return, Roosters sweat on James Tedesco](https://www.goldcoastbulletin.com.au/sport/nrl/supercoach-news/nrl-round-23-late-mail-roosters-sweat-with-james-tedesco-in-doubt-for-bulldogs-clash/news-story/ed64624c53566f667f73bb4ad248feb5)  
  `duckduckgo` 2026-08-02T01:30:31+00:00
- [Defiant Madge answers Broncos question after Reynolds reveal; Roosters’ Teddy call — Late Mail - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-jeremiah-nanai-ruled-out-with-hamstring-injury-surprising-reason-dylan-walker-was-omitted-jonah-pezet-injured-early-mail-team-news-nrl-news/news-story/8b1bcfbd343d2d6947ed218f030cfe66)  
  `google_news_rss` 2026-08-07T01:06:16+00:00
- [2026 NRL Round 23 Predictions - Ladbrokes](https://www.ladbrokes.com.au/blog/2026/08/05/2026-nrl-round-23-predictions/)  
  `google_news_rss` 2026-08-04T23:57:46+00:00
- [NRL Round 23 Team News: Heading East - Bulldogs](https://www.bulldogs.com.au/news/2026/08/04/nrl-round-23-team-news-heading-east/)  
  `google_news_rss` 2026-08-04T05:30:52+00:00
- [NRL Round 23 teams: Munster’s miracle return, Cowboys double blow - Adelaide Now](https://www.adelaidenow.com.au/sport/nrl/supercoach-news/nrl-teams-round-23-latest-injury-news-supercoach-analysis/news-story/a5e81893bf1c655e184c1f680b1b936a)  
  `google_news_rss` 2026-08-04T05:17:39+00:00
- [Inside Critta's leadership evolution as Bulldogs eye statement win](https://www.nrl.com/news/2026/08/07/inside-crittas-leadership-evolution-as-bulldogs-eye-statement-win/)  
  `nrl_news` 2026-08-06T20:01:21+00:00

## Queries the agent wrote

- `Roosters NRL injury OR "late mail" OR "team list" round 23`
- `Bulldogs NRL injury OR "late mail" OR "team list" round 23`
- `Roosters vs Bulldogs NRL round 23 preview`
- `Roosters Bulldogs NRL odds OR price OR favourite`
- `Roosters Bulldogs NRL finals race OR ladder stakes`
- `Roosters Bulldogs NRL`
- `Roosters NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Bulldogs NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Roosters Bulldogs NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 23 Roosters OR Bulldogs`

## Loops

- **Research refine**: not needed (gate passed: True, 18 items with body text)
- **Verifier**: coded checklist passed, LLM audit passed
    - no recalibration needed, so the judgement stands as first written

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | Tedesco's absence is sourced to nrl_news ('Tedesco out') and zero tackle ('James Tedesco Ankle Round 24'); Roosters' six-game streak is sourced to nrl_news ('The Roosters have put together six wins on the trot'). |
| `availability_direction` | pass | Tedesco is correctly described as sidelined/out per sources. |
| `shap_attribution` | pass | Bradley-Terry strength and Elo rating advantage are correctly attributed to the Roosters home win group. |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factor 3 identifies nrl_news regarding Tedesco and team form. |
| `confidence_justified` | pass | Confidence of 0.7 is defensible given the math probability (0.74) and the tempering effect of Tedesco's absence. |
| `driver_proportionality` | pass | The most significant SHAP drivers (Bradley-Terry, Elo) are the ones cited as primary drivers. |
| `omitted_math_signals` | pass | Roosters' top 3 drivers are named; Bulldogs' top drivers all relate to recent form, which is alluded to via 'recent surge into the top eight'. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.