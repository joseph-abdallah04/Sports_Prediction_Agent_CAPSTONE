# Feature Dictionary

Every feature in `feature_store/training_dataset.parquet`: its definition,
what it indicates about a matchup, why it was included (justification),
and its measured univariate signal on the full dataset.

**Conventions used throughout:**

- All features are strictly **pre-match**: computed only from matches that
  finished before kickoff. A match's own stats never appear in its own
  feature row (leakage prevention; see `feature_engineering/Architecture.md`).
- `_diff` features are always **home minus away**. Positive values favour
  the home team.
- Missing values are never imputed (the NaN rule). XGBoost routes missing
  values natively at each tree split, learning the best default direction.
- **Univariate AUC** below is the area under the ROC curve using that single
  feature alone to rank matches by home-win likelihood (0.50 = no signal,
  measured on all 2,311 matches). It understates a feature's value inside
  the full model, where interactions matter, but it is honest evidence of
  standalone predictive power for the report.

Dataset: 2,311 matches (2015-2026), 49 features. Label: `home_win` (1/0),
base rate 0.563. Draws (9) and phantom COVID games (4) are excluded at
Stage 1.

## Identifier columns (not model features)

`match_id`, `season`, `round_number`, `start_time`, `home_team`,
`away_team`, `venue`. Kept for traceability, joins, and chronological
train/test splitting; never fed to the model.

---

## Pillar A: Power ratings (long-term team quality)

These are the three strongest features in the dataset and the model's
backbone. They answer "which team is fundamentally better?" using three
mathematically distinct lenses, so their errors are partially independent
and XGBoost can exploit disagreements between them.

### `elo_diff` — univariate AUC 0.682 (strongest feature)

**Definition.** Difference in rolling Elo rating. Every team starts at 1500
in round 1 of 2015. After each match the winner takes points from the loser:
`delta = K * (actual - expected)` with K=32, where
`expected_home = 1 / (1 + 10^((elo_away - elo_home)/400))`. At each season
boundary a team's rating is regressed 30% toward the league mean of 1500
(off-season mean reversion).

**What it indicates.** Accumulated team quality where beating strong teams
counts for more than beating weak ones, and an upset transfers more rating
points than an expected result.

**Justification.** Elo is the most validated rating system in sports
forecasting (chess origin; FiveThirtyEight's NFL/NBA Elo; club soccer Elo).
It has three properties that suit the NRL: it is self-correcting (a team in
decline bleeds rating quickly), opponent-adjusted (unlike raw win
percentage), and tunable for roster churn. The off-season regression
encodes a real phenomenon — NRL rosters change materially between seasons
(player movement, coaching changes, salary-cap pressure toward parity), so
last year's dominance only partially carries over. Regressing 30% to the
mean rather than resetting preserves the genuine multi-season signal
(e.g. Penrith 2020-2023) while acknowledging churn. Empirically it is the
single best discriminator in the dataset: home-win rate climbs
monotonically from 25.4% in the worst Elo-decile to 80.1% in the best.

### `bt_diff` — univariate AUC 0.673

**Definition.** Difference in Bradley-Terry log-strength. The Bradley-Terry
model assumes `P(i beats j) = s_i / (s_i + s_j)` and finds the strength
vector `s` that maximises the likelihood of all observed results. Refit
before every round on all prior matches via the MM (minorisation-
maximisation) algorithm, with each match weighted by recency:
`weight = 0.5^(age_days / 365)` (1-year half-life).

**What it indicates.** Pure pairwise team strength inferred jointly from
the entire result graph, rather than accumulated incrementally.

**Justification.** Bradley-Terry complements Elo precisely because of how
it differs: Elo is *path-dependent* (the order of results matters and early
games are never revisited), whereas Bradley-Terry refits the *entire
history simultaneously* every round, so a team's rating reflects the
full transitive web of "A beat B who beat C". The exponential time decay
keeps it responsive to the current squad. In a 17-team league where teams
only meet once or twice a season, this transitive pooling of evidence is
valuable — Elo and BT agree most of the time, and the cases where they
disagree are informative to the model.

### `pythag10_diff` — univariate AUC 0.668

**Definition.** Difference in Pythagorean expectation over each team's
previous 10 games: `PF^2.5 / (PF^2.5 + PA^2.5)` where PF/PA are total
points for/against in the window. NaN until a team has played one game.

**What it indicates.** The win rate a team's scoring margin says it
*should* have — a de-noised measure of underlying performance level.

**Justification.** Bill James's Pythagorean expectation (baseball, since
adapted to every major sport) rests on a robust empirical finding: points
margin predicts future wins better than past wins do, because close-game
results are substantially luck. A team that is 7-3 with a points
differential of zero is much weaker than its record; Pythagorean
expectation catches exactly this. Using a 10-game rolling window makes it
a medium-term form measure that bridges the long-memory ratings (Elo/BT)
and the short 3/5-game form windows. The exponent 2.5 follows published
rugby league fittings (typical range 2.0-2.7) and is configurable in
`ratings.py`.

---

## Pillar B: Environmental context

Match circumstances that shift win probability independently of team
quality. Individually modest, these are exactly the kind of marginal,
interaction-heavy variables gradient boosting exploits (e.g. short rest
*and* interstate travel together).

### `ctx_venue_hga` — univariate AUC 0.566

**Definition.** Historical home-win rate at this specific venue, using
prior matches only, with Beta smoothing toward a fixed prior of 0.55
(strength 10 — i.e. a venue with no history starts at the league-typical
rate and needs ~10 games to pull meaningfully away).

**What it indicates.** How strong home advantage actually is *at this
ground*, rather than a binary home/away flag.

**Justification.** Home advantage in the NRL is real (56.3% home-win rate
in this dataset) but it is not uniform: fortress venues with hostile
crowds, unusual dimensions, or long travel for visitors (Suncorp,
Townsville, Auckland) out-perform neutral-ish or shared Sydney grounds
where away fans attend easily. Quantifying the venue, as specified in the
project Overview, lets the model scale its home-advantage assumption per
ground. The fixed 0.55 prior (a constant, not computed from this dataset)
keeps the feature leak-free. The smoothing prevents small-sample venues
(one-off regional games) from producing extreme values.

### `ctx_rest_days_home` / `ctx_rest_days_away` / `ctx_rest_days_diff` — AUC 0.503 / 0.522 / 0.521

**Definition.** Days since each team's previous match, and the difference.
NaN for a team's first recorded game. Off-season gaps appear as large
values, which doubles as a "round 1" indicator.

**What it indicates.** Physical recovery state. NRL is among the most
attritional contact sports; a 5-day turnaround versus an 8-day one is a
material difference in recovery, preparation time, and selection freedom.

**Justification.** Short turnarounds are a documented performance drag in
rugby league (sports-science literature on muscle damage markers post-match
shows recovery extending past 48-72 hours). The *differential* matters
more than the absolute: a 5-day team meeting a 9-day team is the adverse
scenario. Interestingly the away side's rest (AUC 0.522) carries more
standalone signal than the home side's (0.503) — consistent with rest
compounding travel fatigue. Kept as three columns so XGBoost can use
either absolute fatigue or the mismatch.

### `ctx_travel_away` — univariate AUC 0.505

**Definition.** 1 if the venue's state/country differs from the away
team's home state. Computed in Stage 1 from a hardcoded venue-to-state
dictionary covering all 66 venue names in the data (NSW, QLD, VIC, ACT,
SA, WA, NT, NZ, USA, UK — including legacy/sponsor renames such as ANZ →
Accor Stadium, 1300SMILES Stadium, Lottoland).

**What it indicates.** Whether the away team crossed a state or national
border: flights, hotels, time-zone shifts (Perth, Las Vegas), and broken
routine.

**Justification.** Travel fatigue is a standard covariate in professional
sports modelling. The flag's standalone AUC is small because it correlates
with which *teams* are involved (Storm and Raiders always trigger it —
the only VIC/ACT clubs), and the rating features already absorb team
identity. Its value is in interactions: travel x short rest, travel x
Warriors at home (the away side faced a trans-Tasman flight). The
per-away-team trigger rates validated the dictionary: Storm/Raiders 100%,
Warriors 96%, Queensland clubs 60-73%, Sydney clubs 36-47%.

### `ctx_weather` — categorical (fine / cloudy / rain / indoor / unknown)

**Definition.** Raw NRL weather string normalised into five categories
("Showers", "Light Rain", "Rain and Thunder" → `rain`; "Partly Cloudy" →
`cloudy`; missing → `unknown`). Stored as a pandas category; XGBoost
consumes it natively via `enable_categorical`.

**What it indicates.** Playing conditions. Wet weather suppresses
expansive attack, raises error rates, and compresses scorelines — which
shifts win probability toward grinding, low-error teams.

**Justification.** The Overview specifies weather modifiers, and the data
shows a real (modest) effect: home-win rate drops from 56.7% in fine
conditions to 53.6% in rain — rain is a mild equaliser, consistent with
the idea that it adds variance and blunts skill differences. The honest
limitation (documented in `Data_Quality_Findings.md`): weather is missing
in ~36% of matches, including nearly all of 2023-24, so `unknown` is an
explicit category rather than a guess. Within-match interactions (e.g.
rain x completion-rate form) are available to the model where the data
exists. A future enhancement is an external weather join by venue/date.

---

## Pillar C: Granular telemetry form (short-term, rolling 3 & 5 games)

Each stat produces `form3_<stat>_diff` and `form5_<stat>_diff`: rolling
means over each team's previous 3 and 5 games (shifted one game so a match
never sees itself), differenced home minus away. Two windows let the model
weigh "hot right now" (3) against "sustained form" (5) — when the two
disagree, the trajectory itself is information.

**Why rolling form at all?** Ratings (Pillar A) move slowly by design.
Form features capture *how* a team has been playing in the last fortnight,
in process terms rather than results terms. Process stats are less noisy
than results: a team can win ugly twice while its underlying metrics decay.

| Stat | Best AUC (form5) | What it indicates and why it is included |
| --- | --- | --- |
| `points_against` | 0.648 | Defensive output — the strongest form feature, consistent with the rugby league axiom that defence wins premierships. Conceding points is a more stable team trait than scoring them (attack depends more on opposition and luck), which the data confirms: points-against (0.648) outranks points-for (0.598). |
| `all_run_metres` | 0.623 | Total territory gained with ball in hand. The best single proxy for sustained forward dominance — winning the metres battle means playing in the opponent's half, forcing repeat sets and short kicks. Second-strongest form feature. |
| `points_for` | 0.598 | Attacking output. Complements points-against; together they encode recent margin and its split. |
| `line_breaks` | 0.595 | Clean breaches of the defensive line — attacking incision quality, more skill-driven and less volume-driven than metres. |
| `possession_pct` | 0.591 | Share of the ball. Field position and possession compound: more ball means more chances and a rested defence. |
| `tackle_breaks` | 0.591 | Individual dominance in contact — beating defenders one-on-one, a leading indicator of attacking potency even when points haven't followed yet. |
| `support_plays` | 0.590 | **Proxy feature**: sum of per-player `lineBreakAssists` + `tryAssists` (the NRL payload has no direct "supports" stat). Measures creative connection — players in position to assist breaks and tries. A genuine mid-tier signal despite being a proxy. |
| `post_contact_metres` | 0.571 | Metres gained *after* first contact — "the grind" from the Overview. Measures forward-pack dominance and effort beyond scheme; teams that win post-contact metres bend the defensive line and earn quick play-the-balls. |
| `missed_tackles` | 0.562 | Defensive integrity at the individual level. Missed tackles precede conceded points; rising counts signal fatigue or effort decay before the scoreboard shows it. |
| `forced_drop_outs` | 0.545 | Repeat-set generation via attacking kicks — sustained pressure converted into field position. ~10% NaN (era recording gaps), left missing per the NaN rule. |
| `effective_tackle_pct` | 0.539 | Tackle quality (completed cleanly vs slipped/offloaded out of). Complements missed tackles by measuring ruck control rather than raw misses. |
| `completion_rate` | 0.529 | Sets completed without error — the classic "completion footy" discipline measure. **2019+ only** (62-76% missing 2015-18, an era gap left as NaN, never imputed). Modest standalone but interacts with weather (wet-weather completion is the Overview's hypothesis). |
| `play_the_ball_speed` | 0.518 | Average ruck speed (lower = faster). Fast play-the-balls compound into tired, retreating defences; a tempo/dominance indicator from the Overview's "grind" pillar. |
| `errors` | 0.515 | General ball security. 2015 has no team-level stat; reconstructed exactly by summing per-player `errors` (aggregation of raw data, not imputation). |
| `penalties_conceded` | 0.512 | Discipline volume. Standalone signal is weak because referees and game state drive variance, but it feeds the model alongside the timeline-based discipline features below. |
| `kicking_metres` | 0.511 | Kicking-game territory. Weak alone (volume kicking can reflect being trapped in your own half), but interacts with metres and possession. |
| `offloads` | 0.514 | Second-phase play generation. Style-dependent (high-risk, high-reward), so weak globally — but that is exactly the kind of conditional feature trees can use. |

**A note on weak features.** Several form features sit at AUC 0.51-0.54.
They are retained deliberately: univariate AUC measures standalone signal,
but gradient boosting builds interactions (penalties x weather, offloads x
possession), and XGBoost's column subsampling plus SHAP attribution in
Phase 3 will reveal which earn their place. Pruning is a Phase 3 decision
to be made with proper validation, not at dataset-construction time.

**A removed feature.** `decoy_runs` (planned proxy via per-player
`lineEngagedRuns`) was removed after validation: the field exists in the
NRL schema but is **zero in all 2,311 matches** — never populated. It
contributed exactly AUC 0.500 (pure noise) and was cut from the pipeline.
No direct decoy-run measure exists in the data.

---

## Pillar D: Momentum and fatigue (timeline-derived, rolling 5 games)

These features exist because of the granular `timeline` array (every
event time-stamped in `gameSeconds`) — information unavailable in ordinary
box scores and a key differentiator of this dataset.

### `mom5_last20_net_points_diff` — univariate AUC 0.596

**Definition.** Net points (own minus opponent) scored in regulation
gameSeconds 3600-4800 (the final 20 minutes), averaged over the last 5
games. Extra-time scoring is excluded so golden-point chaos doesn't
contaminate the fatigue measure.

**What it indicates.** Late-game fitness and composure: who finishes
games stronger.

**Justification.** The Overview's "Late-Game Fatigue Rating". Rugby league
games are frequently decided after the 60th minute when rotations are
exhausted; a team that consistently wins the final quarter has superior
conditioning, bench impact, or game management. This is invisible to
full-game margins (a +6 result built on a dominant last 20 differs from a
+6 result surviving a late collapse) and it is the strongest momentum
feature at AUC 0.596 — comparable to mid-tier form features.

### `mom5_first_to_score_rate_diff` — univariate AUC 0.552

**Definition.** Share of the last 5 games where the team scored first
(any scoring event, ranked by `gameSeconds`).

**What it indicates.** Early-game execution: quality of starts.

**Justification.** The Overview's early-momentum hypothesis. Scoring first
correlates with winning (scoreboard pressure changes the trailing team's
risk appetite), and *habitually* scoring first indicates strong starts —
preparation and early-set execution — which is distinct information from
where a team ends up at full time.

### `mom5_penalty_gap_seconds_diff` — univariate AUC 0.515

**Definition.** Mean seconds between a team's *conceded* discipline events
within a game (Penalty events pre-2020; Penalty + SetRestart +
RuckInfringement from 2020, when the six-again rule moved much ruck
discipline out of formal penalties), averaged over the last 5 games.
Larger gap = better discipline. Event `teamId` semantics were verified
against the "Penalties Conceded" team stat: 106/106 checked matches agree
that `teamId` is the conceding team.

**What it indicates.** Average discipline tempo — how frequently a team
hands over possession or field position.

### `mom5_penalty_cluster_rate_diff` — univariate AUC 0.518

**Definition.** Count of discipline *collapses* per game — non-overlapping
bursts of 3+ conceded discipline events within any sliding 5-minute
(300-second) window — averaged over the last 5 games.

**What it indicates.** Composure under pressure. Conceding eight penalties
evenly across 80 minutes is survivable; conceding three in four minutes
usually means a team pinned on its line, a sin-bin risk, and points
conceded.

**Justification (both discipline features).** The Overview's "Penalty
Clusters" pillar. The pair separates discipline *volume* (gap) from
discipline *clustering* (bursts) because they fail differently: a team can
have mediocre average discipline but rarely collapse, or look fine on
average while melting down in patches. Both are deliberately era-consistent
(the six-again rule changed what referees blow penalties for in 2020;
including SetRestart/RuckInfringement keeps the conceded-infringement
stream comparable across the rule change). Standalone AUCs are modest —
discipline is partly game-state-driven — but they are unique,
timeline-only information no box-score feature duplicates.

---

## Pillar E: Roster resilience (rolling 5 games)

### `wl5_top3_run_metre_share_diff` — univariate AUC 0.522
### `wl5_top3_tackle_share_diff` — univariate AUC 0.507

**Definition.** The share of a team's total run metres (respectively,
tackles made) carried by its top 3 players in each game, averaged over the
last 5 games. Computed from per-player stats (verified identical schema
across all 12 seasons).

**What it indicates.** Workload concentration. Low share = distributed
contribution; high share = dependence on a few individuals.

**Justification.** The Overview's mathematical-resilience hypothesis: a
team where three players produce 40% of all run metres is fragile — an
injury, sin-bin, or targeted defensive plan removes a disproportionate
share of its output, whereas a distributed team degrades gracefully. This
also functions as an indirect star-dependence measure that requires no
player-identity modelling. The run-metre version carries more signal than
the tackle version (attacking workload concentrates on key forwards;
tackle workload is structurally spread by defensive systems). Like the
context features, these are interaction fodder more than standalone
predictors.

---

## Known caveats (for the report's limitations section)

- Rolling features are NaN for a team's first game(s): early 2015 rounds
  and the Dolphins' 2023 entry are the main pockets (worst-case ~4% of a
  season's rows). Handled natively by XGBoost; optionally excludable with
  `build_dataset.py --min-history N`.
- `completion_rate` is era-gated (2019+). `ctx_weather` is `unknown` for
  ~36% of matches. Neither is imputed.
- Draws are excluded end-to-end (strictly binary outcomes), so drawn games
  also do not contribute to rating/form history — an accepted trade-off
  affecting ~1% of games.
- Features are correlated within pillars (by design — three ratings, two
  windows per stat). Fine for prediction with tree ensembles; for SHAP
  narration in Phase 3, correlated features will share credit, which is
  worth a sentence in the report.

## Reference benchmark

Smoke test (chronological split: train 2015-2023 = 1,778 matches, test
2024-2026 = 533 matches, near-default XGBoost): **AUC 0.630, accuracy
62.7%** vs the 56.9% always-pick-home baseline (+5.8 points). Published
academic NRL/AFL prediction work typically reports 60-67% accuracy, so the
dataset supports competitive performance before any Phase 3 tuning,
calibration, or feature selection.
