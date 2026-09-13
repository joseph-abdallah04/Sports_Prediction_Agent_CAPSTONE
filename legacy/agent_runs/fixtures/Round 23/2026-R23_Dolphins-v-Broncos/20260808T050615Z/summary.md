# Dolphins v Broncos

- **Run**: `20260808T050615Z-aa39550b`
- **When**: 2026-08-08T05:06:15.903078+00:00
- **Model**: ollama/gemma4:31b-mlx
- **Kickoff**: 2026-08-08T17:30:00+10:00 at Suncorp Stadium (round 23)

## Verdict

**Dolphins** to win, confidence 74%.

> The Dolphins are strong favourites based on a significant ladder gap (5th vs 16th) and superior underlying quality, evidenced by a +54% Pythagorean expected-win gap. While the Broncos have shown slight defensive improvement in recent points against metrics, this is outweighed by the loss of key playmaker Adam Reynolds to concussion. With the Dolphins chasing a top-four finish and Brisbane's season effectively over, the momentum heavily favours the home side.

### Key factors

- **math** — The model shows a strong home edge driven by an Elo advantage (+125 points) and superior Pythagorean form (last 10 games), which indicates a +54% expected-win gap.
- **research** — Broncos playmaker Adam Reynolds is ruled out with a concussion, forcing Tom Duffy into the halfback role (NRL Team List Round 23 v Dolphins - Brisbane Broncos).
- **scene** — The official standings confirm a stark contrast in form, with the Dolphins holding 12 wins compared to the Broncos' 6.
- **math** — Minor offsets favouring Brisbane include recent points against trends (3-game and 5-game), though these carry low weight relative to the overall model net.

## What the maths said

- Prediction: **Home Win**
- P(Dolphins win) = **0.7434**

| Favouring Dolphins (home) | Favouring Broncos (away) |
| --- | --- |
| Elo rating advantage (+125 points) — contribution 0.224 (16% of total) | 3-game form: points against (+14.67) — contribution 0.086 (6% of total) |
| Ladder points differential per game (+12.9 points) — contribution 0.144 (10% of total) | 5-game form: penalties conceded (-2.20) — contribution 0.041 (3% of total); CONFLICT: the raw value on its own favours the home side — the model still nets it toward away here |
| Pythagorean form (last 10) (+54% expected-win gap) — contribution 0.133 (10% of total) | 5-game form: points against (+5.80) — contribution 0.037 (3% of total) |
| Bradley-Terry strength advantage (+0.26 log-strength) — contribution 0.127 (9% of total) | Head-to-head record (last 5) (20% to the home side) — contribution 0.034 (2% of total) |
| 5-game form: all run metres (+169.00) — contribution 0.105 (8% of total) | Travel-distance advantage (-22 km for away) — contribution 0.023 (2% of total) |

- Attribution balance: leans **home** (home 1.0478, away 0.3522)
- Value/contribution conflicts:
  - 5-game form: penalties conceded (-2.20)

## Ladder standings

As at round 23 ([nrl.com](https://www.nrl.com/ladder/?competition=111&season=2026&round=23)).

- **Dolphins** — 5th · 12-0-7 · PD +90 (+4.74/g)
- **Broncos** — 16th · 6-0-13 · PD -156 (-8.21/g)

- Higher on ladder: **Dolphins**
- Points-difference favours: **Dolphins** (home−away PD/game gap: 12.95)

## What the research found

16 items kept (dropped: stale 63, wrong_round 5, noise 8, irrelevant 15, duplicate_url 4, no_body 5).

- [NRL Late Mail: Round 23 - Rabbitohs lose Graham; Best sidelined](https://www.nrl.com/news/2026/08/05/nrl-late-mail-round-23---origin-guns-return-as-finals-loom/)  
  `nrl_news` 2026-08-08T04:06:17+00:00
- [NRL Team Lists: Round 23](https://www.nrl.com/news/2026/08/04/nrl-team-lists-round-23/)  
  `nrl_news` 2026-08-04T06:00:45+00:00
- [NRL Team List Round 23 v Dolphins - Brisbane Broncos](https://www.broncos.com.au/news/2026/08/04/nrl-team-list-round-23-v-dolphins/)  
  `google_news_rss` 2026-08-04T05:32:06+00:00
- [Injuries NRL Casualty Ward: Panthers' Yeo blow; Tupouniua sidelined again 28 mins ago](https://www.nrl.com/news/2026/01/01/nrl-casualty-ward-how-your-club-is-shaping-heading-into-2026/)  
  `nrl_news` 2026-08-08T04:38:02+00:00
- [Super Saturday: Storm v Sea Eagles; Dolphins v Broncos; Rabbitohs v Eels](https://www.nrl.com/news/2026/08/08/super-saturday-storm-v-sea-eagles-dolphins-v-broncos-rabbitohs-v-eels/)  
  `nrl_news` 2026-08-08T04:01:29+00:00
- [Match Preview Dolphins v Broncos: Katoa ready to shine; Duffy steps up](https://www.nrl.com/news/2026/08/04/dolphins-v-broncos-katoa-ready-to-shine-duffy-steps-up/)  
  `nrl_news` 2026-08-07T07:36:03+00:00
- [Match Preview: Round 23 – Dolphins v Broncos - Official website of The Dolphins](https://www.dolphinsnrl.com.au/news/2026/08/07/match-preview-round-23--dolphins-v-broncos/)  
  `google_news_rss` 2026-08-07T05:57:29+00:00
- [Dolphins vs Broncos Preview & Betting Tips: NRL Round 23 2026 - Before You Bet](https://www.beforeyoubet.com.au/dolphins-vs-broncos-preview-betting-tips-nrl-round-23-2026)  
  `google_news_rss` 2026-08-07T05:28:04+00:00
- [Broncos Broncos aiming to create major disruptions in Dolphins derby](https://www.nrl.com/news/2026/08/06/broncos-aiming-to-create-major-disruptions-in-dolphins-derby/)  
  `nrl_news` 2026-08-05T21:01:21+00:00
- [Dolphins v Broncos: Round 23 - NRL.com](https://www.nrl.com/news/2026/08/05/dolphins-v-broncos-round-23/)  
  `google_news_rss` 2026-08-05T04:04:43+00:00
- [Dolphins vs Broncos - Round 23, 2026 - Live Scores & Stats - Match Centre - Zero Tackle](https://www.zerotackle.com/dolphins-broncos-round-23-2026-mc10396510-236516/)  
  `google_news_rss` 2026-08-02T19:43:04+00:00
- [Match Preview Raiders v Knights: Sasagi returns; Frizell the milestone man](https://www.nrl.com/news/2026/08/04/raiders-v-knights-sasagi-returns-frizell-the-milestone-man/)  
  `nrl_news` 2026-08-08T04:06:56+00:00
- [NRL 2026: Confirmed lineups, results for Round 23 - sportingnews.com](https://www.sportingnews.com/au/rugby-league/news/nrl-team-lists-round-23-2026-lineups-injuries-results/b358f066284f90e03d93a242)  
  `google_news_rss` 2026-08-07T02:22:53+00:00
- [Match Preview Storm v Sea Eagles: Munster back on deck; Laiafi to start](https://www.nrl.com/news/2026/08/04/storm-v-sea-eagles-munster-back-on-deck-wakeham-returns/)  
  `nrl_news` 2026-08-08T03:36:17+00:00
- [Match Preview Bulldogs v Cowboys: Hopoate sidelined; Forwards shuffled](https://www.nrl.com/news/2026/08/05/bulldogs-v-cowboys-no-changes-for-wiliame-forwards-shuffled/)  
  `nrl_news` 2026-08-08T01:20:08+00:00
- [Wayne confirms crushing Souths blow after training mishap; sad Reynolds update - Fox Sports](https://www.foxsports.com.au/nrl/nrl-premiership/nrl-2026-jeremiah-nanai-ruled-out-with-hamstring-injury-surprising-reason-dylan-walker-was-omitted-jonah-pezet-injured-early-mail-team-news-nrl-news/news-story/8b1bcfbd343d2d6947ed218f030cfe66)  
  `google_news_rss` 2026-08-07T13:42:11+00:00

## Queries the agent wrote

- `Dolphins NRL injury OR "late mail" OR "team list" round 23`
- `Broncos NRL injury OR "late mail" OR "team list" round 23`
- `Dolphins vs Broncos NRL round 23 preview`
- `Dolphins Broncos NRL odds OR price OR favourite`
- `Dolphins Broncos NRL finals race ladder stakes form`
- `Dolphins Broncos NRL`
- `Dolphins NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Broncos NRL injury OR sidelined OR suspension OR judiciary OR "team list" OR "late mail"`
- `Dolphins Broncos NRL preview OR form OR motivation OR derby OR "must win" OR bye`
- `NRL round 23 Dolphins OR Broncos`

## Loops

- **Research refine**: not needed (gate passed: True, 16 items with body text)
- **Verifier**: coded checklist passed, LLM audit FAILED
    - The judgement omits several top SHAP drivers from both sides of the model output.
    - recalibrated: home 0.74 → home 0.74

### What the verifier checked

| Check | Verdict | Evidence |
| --- | --- | --- |
| `sourced_claims` | pass | All claims match scene standings (5th vs 16th, 12 wins vs 6) or research articles regarding Adam Reynolds' concussion and the finals race. |
| `availability_direction` | pass | Adam Reynolds is correctly described as ruled out per the research text. |
| `shap_attribution` | pass | Elo and Ladder differential drivers are correctly attributed to the Dolphins from the favouring_Dolphins group. |
| `weather_not_headline` | pass | Weather is not presented as a key factor. |
| `research_used` | pass | Key factor 2 identifies the 'NRL Team List Round 23 v Dolphins - Brisbane Broncos' article. |
| `confidence_justified` | pass | Confidence of 0.74 is within range and justified by ladder gap, injury to Reynolds, and model ratings. |
| `driver_proportionality` | pass | The judgement focuses on the top two SHAP drivers (Elo and Ladder differential). |
| `omitted_math_signals` | fail | Top math signals 'Pythagorean form' (Dolphins), '3-game form: points against', '5-game form: penalties conceded', and '5-game form: points against' (Broncos) are not addressed. |

---

Full detail, including every tool request and response, is in `ledger.json` beside this file. Nothing is omitted there.