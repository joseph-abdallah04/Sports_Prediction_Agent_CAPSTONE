# Key Design Decisions

A running log of the project's engineering crossroads: what was decided,
what was rejected, and why. Newest entries at the bottom. Deep-dive
rationale lives in the linked docs; this file is the index for the report.

---

## DD-01: Scrape nrl.com's embedded JSON instead of using an API or HTML scraping

**Decision.** Extract match data from the `q-data` state-hydration
attribute embedded in nrl.com pages (`vue-match-centre` for matches,
`vue-draw` for fixture discovery).

**Alternatives.** Paid sports-data APIs (cost, licensing); parsing
rendered HTML tables (brittle, far less granular).

**Why.** The embedded payload is the same structured JSON the site's own
frontend consumes: ~36 team stats, 59 per-player stats, and a full
time-stamped event timeline per match — richer than any free alternative,
and parsed with a single JSON decode instead of fragile HTML traversal.

## DD-02: Restrict history to the telemetry era (2015-present)

**Decision.** Backfill 2015-2026 only (~2,300 matches).

**Alternatives.** Deeper history for more training rows.

**Why.** Advanced telemetry (post-contact metres, play-the-ball speed) is
only reliably present from ~2015. Older seasons would add rows but with
mostly-missing features, diluting exactly the granular signal the
Mathematical Engine is built around (see `tools/mathematical_engine/Overview.md`).

## DD-03: One-off backfill and weekly pipeline as separate jobs sharing a scraping toolkit

**Decision.** `historical_data_backfill_etl/` (Job A, run once) is its own
directory; shared logic (polite HTTP client, match-centre extractor) lives
in `nrl_scraping/` for the future weekly job (Job B) to reuse.

**Alternatives.** One combined ETL codebase; or full duplication per job.

**Why.** The jobs have different lifecycles (run-once vs scheduled) and
different discovery logic, but identical extraction. Separating the jobs
keeps them individually simple; sharing the toolkit avoids drift between
two copies of the same scraper.

## DD-04: Data lake holds raw, untransformed JSON only

**Decision.** `data_lake/` stores payloads byte-for-byte as scraped.
Transformed data lives separately in `feature_store/`.

**Why.** Raw data is the one irreplaceable asset. Keeping it pristine
means every transformation decision is reversible — we re-derive features
at will (which paid off when the decoy-runs feature was cut; see DD-12).

## DD-05: Parquet over CSV for all tabular outputs

**Decision.** All transformed tables are Parquet.

**Why.** Compressed, fast, and type-strict — a numeric column cannot
silently become text, which matters for XGBoost compatibility. CSV offers
none of these guarantees.

## DD-06: Two-stage pipeline — post-match facts, then pre-match features

**Decision.** Stage 1 (`flatten.py`) records what *happened* per match;
Stage 2 (`build_dataset.py`) computes what was *knowable before kickoff*,
walking strictly chronologically.

**Alternatives.** Single pass computing features during parsing.

**Why.** The stage boundary IS the leakage boundary, making the no-leakage
guarantee structural and auditable rather than scattered through the code.
Verified with explicit checks (Elo flip test, hand recomputation).
Details: `tools/mathematical_engine/feature_engineering/Architecture.md`.

## DD-07: The NaN rule — never impute missing data

**Decision.** Era-missing telemetry (e.g. completion rate pre-2019,
weather in ~36% of matches) stays NaN / explicit `unknown`.

**Alternatives.** Mean/median imputation; external data joins.

**Why.** XGBoost handles missing values natively by learning a default
split direction; imputation would inject fabricated signal. One exception
on principle: 2015 team errors are *summed exactly* from per-player error
counts — aggregation of real data, not guessing.

## DD-08: Strictly binary outcomes — draws dropped at Stage 1

**Decision.** The 9 drawn matches (and 4 phantom COVID fixtures) never
enter the feature store.

**Trade-off accepted.** Drawn games also vanish from Elo/form history
(~1% of matches) — documented rather than hidden.

**Why.** The model is a binary classifier (home win / home loss); at a
0.9% draw rate, modelling a third class would cost more complexity than
it returns.

## DD-09: Hardcoded venue geography, no geocoding service

**Decision.** `flatten.py` owns three static tables: `VENUE_TO_STATE` (all 67
venue names including legacy/sponsor renames), `VENUE_TO_COORDS`, and
`TEAM_HOME_COORDS`. Unknown venues default to no-travel and print a warning.

**Alternatives.** Geocoding API; deriving from venueCity at runtime; deriving
each club's home base from its most frequent historical venue.

**Why.** A fixed venue list does not justify a runtime dependency. Each entry
was verified once against the payload's own `venueCity` field, then frozen as
explicit, reviewable code. Home bases are static rather than data-derived
precisely so they cannot leak information from future fixtures. Validated
empirically: Storm/Raiders trigger the travel flag 100% (only VIC/ACT clubs),
Warriors 96%, Sydney clubs 36-47%.

## DD-10: Three power ratings, not one (Elo + Bradley-Terry + Pythagorean)

**Decision.** Compute all three as separate features.

**Why.** They measure team quality through mathematically different
lenses: Elo is path-dependent accumulation, Bradley-Terry refits the whole
result graph jointly (with recency decay), Pythagorean reads points margin
rather than results. Their disagreements are themselves signal for the
model. All three rank top-3 in univariate AUC (0.682 / 0.673 / 0.668).

## DD-11: Fixed constants for priors (no dataset-derived priors)

**Decision.** Venue home-advantage smoothing uses a fixed 0.55 prior;
Elo off-season regression is a fixed 30% toward 1500.

**Why.** A prior estimated from the full dataset would leak future
information backward in time. Constants cannot leak.

## DD-12: Cut the decoy-runs feature after validation

**Decision.** Removed the planned `decoy_runs` proxy (per-player
`lineEngagedRuns`).

**Why.** Validation showed the source field is zero in all 2,311 matches —
present in the NRL schema, never populated. The feature scored univariate
AUC exactly 0.500 (pure noise). Removing it improved smoke-test accuracy
from 61.0% to 62.7%. Lesson recorded: validate that source fields contain
data, not just that they exist.

## DD-13: Keep weak features; prune in Phase 3, not at dataset construction

**Decision.** Features with univariate AUC 0.51-0.54 (travel, rest days,
discipline, workload) stay in the dataset.

**Why.** Univariate AUC ignores interactions (travel x short rest,
rain x completion rate) — exactly what gradient boosting exploits.
Pruning decisions belong in Phase 3 with proper validation and SHAP
evidence, not before the model exists.

## DD-14: Scraped weather with explicit `unknown`, no external weather API (for now)

**Decision.** Normalise nrl.com's weather field to five categories;
missing becomes the honest category `unknown` (~36% of matches).

**Alternatives.** Joining a historical weather API (e.g. Open-Meteo) by
venue city + date.

**Why.** Scope control for Phase 2. The measured rain effect (home-win
rate 56.7% fine vs 53.6% rain) suggests the external join is a worthwhile
*future* enhancement — recorded in `Data_Quality_Findings.md`.

## DD-15: Plain Parquet with full weekly rebuilds — no Iceberg

**Decision.** The weekly pipeline will re-run the full Stage 1 + Stage 2
build (~seconds) rather than appending to tables via a table format like
Apache Iceberg.

**Alternatives.** Apache Iceberg (appendable tables over Parquet);
partitioned Parquet (one file per season).

**Why.** Parquet files are immutable, so appends genuinely require either
a table format or a rewrite — but our entire dataset is ~2,300 rows
(megabytes), and a full rebuild takes ~4 seconds. Iceberg solves
concurrent-writer, petabyte-scale problems we do not have, at the cost of
a catalog, a new dependency, and a second code path. Rebuilds also
guarantee the stateful features (Elo, Bradley-Terry) always come from the
single trusted chronological pass. XGBoost is unaffected either way — it
trains on the in-memory DataFrame, never on the storage format. Upgrade
path if scale ever demands it: season-partitioned Parquet first, Iceberg
only after that.

## DD-16: Generated data stays out of git

**Decision.** `data_lake/`, `feature_store/`, and `models/` are gitignored.

**Why.** Hundreds of MB of regenerable artifacts don't belong in version
control; code, configuration, and documentation do. Everything in those
folders is reproducible from the pipelines (`backfill.py`,
`build_dataset.py`, `train.py`).

## DD-17: Log loss as the tuning objective (not accuracy)

**Decision.** Optuna minimises mean log loss across folds.

**Alternatives.** Maximise accuracy or AUC.

**Why.** Log loss is a proper scoring rule that rewards well-calibrated
probabilities. The LLM Orchestrator reasons with the probability itself
(e.g. "74% home win"), not just the binary pick, so probability quality is
the thing to optimise. Accuracy ignores confidence; AUC ignores calibration.

## DD-18: Expanding-window chronological cross-validation

**Decision.** Tuning/calibration validate with expanding windows (train
through season S, validate on S+1, for S+1 in 2021-2024); 2025-2026 is a
final untouched holdout.

**Alternatives.** Random k-fold cross-validation.

**Why.** Random folds let the model validate on matches that occurred before
others in its training set - future leaking into past - producing
optimistic, unrealistic scores. Expanding windows replicate production: only
the past is known. The holdout being untouched makes the reported 2025-2026
numbers an honest estimate of next-season performance.

## DD-19: Tune occasionally, train weekly

**Decision.** Hyperparameter search is a manual, occasional job; weekly
retraining reuses the saved `best_params.json`.

**Why.** Best hyperparameters reflect the dataset's shape (~2,400 rows, 61
features, NRL noise), which one new round of ~8 matches does not change.
Re-tuning weekly would burn compute to rediscover near-identical settings
and could introduce week-to-week instability. Re-tune each off-season or
after significant feature changes.

## DD-20: Two model fits - served model on all data, evaluation model on a holdout

**Decision.** `train.py` fits the production model on ALL data (2015-2026);
`evaluate.py` separately fits on development data (<=2024) to score the
untouched 2025-2026 holdout.

**Why.** These serve different goals. The deployed model should be maximally
informed (use every match). Honest generalisation metrics require data the
model never saw. Conflating them either cripples the served model or inflates
the reported numbers. Two purposes, two fits.

## DD-21: Sigmoid (Platt) calibration as default

**Decision.** Default probability calibration is sigmoid; isotonic is
available and compared in `evaluate.py`.

**Why.** Isotonic regression is more flexible but overfits small calibration
sets (~500 out-of-time points here). On the 2025-2026 holdout sigmoid beat
isotonic on both Brier (0.230 vs 0.233) and log loss (0.651 vs 0.662),
confirming the theoretical expectation.

## DD-22: Bradley-Terry refit per kickoff time, not per round

**Decision.** Changed BT to refit at each distinct kickoff time using all
strictly-earlier matches (was: one fit per season-round block).

**Why.** The per-round version gave every match in a round the same BT
snapshot from before the round started. When the inference path rebuilds a
mid-round fixture "as of its exact kickoff", earlier same-round matches are
now visible, so the rebuilt `bt_diff` diverged from the stored training value
- the parity test caught this (2/5 mismatches on `bt_diff`). Refitting per
kickoff makes BT strictly pre-match like Elo and form, so training and
inference are provably identical (parity test passes 5/5). Cost: dataset
rebuild rose from ~4s to ~22s - acceptable for an occasional job.

## DD-23: Upcoming-fixture features via a synthetic row through Stage 2

**Decision.** `inference.py` predicts future games by appending one
synthetic, unplayed row to the historical flat table and running the
existing Stage 2 feature code, rather than reimplementing feature math for
serving.

**Why.** A second feature implementation for inference is the classic source
of train/serve skew. Reusing the exact training code path makes drift
impossible by construction, and a parity test asserts equality on historical
fixtures (passes 5/5).

## DD-24: Weekly ETL (Job B) as a separate orchestrator package

**Decision.** `weekly_incremental_etl/run.py` discovers completed matches from
nrl.com draw pages, scrapes only URLs not already in the data lake (dedup via
backfill + weekly manifests and on-disk `nrl_match_{id}.json` files), then
full-rebuilds features and calls `model.train`. Does not touch
`backfill_manifest.json` or run `model.tune`.

**Why.** Same separation rationale as DD-03: one-off backfill vs ongoing
weekly job. Draw-page auto-discovery replaces the Overview's manual URL feed.
Full rebuild per DD-15 keeps stateful features correct. A single CLI is the
operator runbook for each round.

## DD-25: Shared `predict_fixture()` with artifact hot-reload

**Decision.** Both the `model.predict` CLI and the MCP gateway tool
`predict_match` call the same `predict_fixture()` in `model/serving.py`.
That layer hot-reloads model artifacts by watching the modification time of
`models/metrics.json` before each prediction. Serving never triggers
scraping, feature rebuilds, or retraining.

**Alternatives.** Separate prediction code per interface; restarting a
long-lived process after each weekly ETL; an endpoint that triggers the ETL.

**Why.** One shared code path means CLI and agent predictions cannot diverge
(same anti-drift philosophy as DD-23). Watching `metrics.json` — written
*last* by `train.py` — makes the weekly artifact swap effectively atomic.
Keeping the ETL out of the serving path preserves decoupling: tools serve
whatever is in `models/`; the operator refreshes it on their own schedule.

## DD-26: MCP gateway instead of per-tool FastAPI

**Decision.** Expose scene, research, and math through one local MCP server
(`tools/mcp_gateway/`) that calls library entrypoints in-process. Remove per-tool
FastAPI apps (`:8000` / `:8001` / `:8002`). Keep CLIs for human testing and
demos.

**Alternatives.** Keep three FastAPI servers; agent shells out to CLIs;
HTTP-only gateway without MCP.

**Why.** The agent needs one discovery surface and typed tools; three HTTP
ports duplicated CLI behaviour and added ops overhead once MCP was chosen.
CLIs remain the operator path. Historical Phase 4b FastAPI notes remain under
`plans/math_engine_plans/phase_4b_fastapi_endpoint.plan.md` as superseded
context.


## DD-27: Fact tools under `tools/`

**Decision.** Place `mathematical_engine/`, `fixture_scene/`, `qualitative_research/`,
and `mcp_gateway/` under a top-level `tools/` directory.

**Alternatives.** Leave packages at repo root; nest only the MCP gateway.

**Why.** Tidier Capstone layout: fact tools vs future `agent/` at the root.
Sibling path deps inside `tools/` stay simple; operator commands use
`cd tools/<package>`.

## DD-28: Two-pass relevance in qualitative research

**Decision.** `filter_items()` no longer discards an article that mentions
neither fixture team; it *defers* it. Deferred items get their body fetched,
then run through the same relevance test a second time
(`promote_deferred_with_bodies`). Only then are they kept or dropped.

**Alternatives.** Fetch every article's body up front (slow, and most are
irrelevant); loosen the team-mention rule (lets unrelated NRL news through).

**Why.** The first pass could only see the title, snippet, and category,
because bodies were fetched *after* filtering. Any article that named the
fixture only in its text — routine for official club pages and round wraps —
was dropped before its body existed. On the Titans v Cowboys test fixture this
single change recovered 4 genuinely relevant articles. Deferral is capped
(15 extra fetches) so the cost stays bounded.

## DD-29: Agent-authored queries are merged with the default templates

**Decision.** When the Orchestrator supplies `queries`, they are unioned with
the built-in templates (capped at 10 total) rather than replacing them.
Supersedes point 2 of `agent/adrs/0003-agent-authored-research-queries.md`.

**Alternatives.** Keep replacement (original behaviour); ignore agent queries.

**Why.** Replacement meant one weak LLM query plan silently disabled all the
tuned injury / Late Mail / team-list coverage that the research gate checks
for — the agent could lose recall by exercising its own agency. Merging keeps
the agency (its queries run first and steer discovery) while guaranteeing the
availability floor. Combined with DD-28 and wider per-query result caps, kept
items on the test fixture went from 3 to 13.

## DD-30: Ship new features only if they beat the holdout, measured by an A/B

**Decision.** Twelve features were added: season-to-date ladder position, win
rate and points differential per game; head-to-head record, margin and sample
size over the last five meetings; short-turnaround flags; and travel distance
in kilometres. They shipped only after `model.feature_ab` showed a gain on the
untouched 2025-2026 holdout, averaged over 8 random seeds.

**Result.** Holdout AUC 0.640 → 0.651, log loss 0.659 → 0.651, accuracy
62.6% → 63.0%. `ladder_pts_per_game_diff` is now the strongest feature by
global SHAP, ahead of `bt_diff` and `elo_diff`.

**Alternatives.** Ship on face validity (the features are obviously sensible);
judge by a single train/test fit.

**Why.** "Obviously sensible" is how you overfit 2,366 rows. A single fit is
not enough either: seed alone moves holdout AUC by roughly ±0.003, the same
order as the effect being measured, so the A/B averages across seeds and holds
hyperparameters, splits and seeds identical between arms. Accuracy actually
*fell* in one arm of the retuned A/B while AUC and log loss both improved —
recorded here rather than hidden, and consistent with DD-17: probability
quality is the objective, not threshold accuracy.

## DD-31: Judgement confidence is anchored to the calibrated model probability

**Decision.** The judge must set confidence within 0.10 of the model's
probability for the side it picks, never above 0.85, and never above 0.60 when
picking against the model. A deterministic check in `verifier.py` enforces
this, alongside two grounding rules: weather may not be a key factor unless a
weather feature appears in the SHAP drivers, and at least one key factor must
come from research whenever research returned usable items.

**Alternatives.** Leave confidence to the LLM's judgement; enforce only via the
verifier prompt.

**Why.** The model scores ~63% accuracy on unseen seasons, so an unanchored LLM
confidence is decoration rather than information. Earlier runs also showed the
judge promoting match-day weather to a headline factor while SHAP ranked it
nowhere — the scene reports weather, so the LLM reaches for it. Coded checks
are used in preference to prompt instructions wherever the rule is decidable
from the ledger, because the verifier LLM is exactly as fallible as the judge.
Details: `agent/adrs/0006-grounded-judgement-and-confidence.md`.

## DD-32: Measure the agent forward, a whole round at a time

**Decision.** `agent_app.harness run` predicts every fixture in a round from
the nrl.com draw and writes the predictions to disk before kickoff;
`agent_app.harness score` reads that file back after the games and scores the
agent, the raw math model, and the always-back-the-home-team baseline on
accuracy, Brier score and log loss.

**Alternatives.** Hand-picking fixtures each week; backtesting the agent over
historical rounds.

**Why.** One fixture at a time is an anecdote, and hand-picking fixtures is how
you accidentally report your best ones. Historical backtests are impossible for
the *agent* specifically: the research channels return today's news, so there
is no honest way to reconstruct what was knowable before a 2023 kickoff. The
math model can be backtested properly (DD-18, DD-20); the agent can only be
measured forward. Writing predictions before kickoff and scoring from a
separate command makes back-fitting structurally impossible.
Details: `agent/adrs/0007-round-results-harness.md`.

## DD-33: The verifier is given the evidence it is asked to check

**Decision.** The LLM verifier's audit packet includes each research article's
body excerpt (12 items x 900 characters), not just its headline. The judgement
prompt additionally tells the judge to read availability news for *direction*,
and the verifier checks that it did.

**Alternatives.** Keep titles only and soften the grounding rule; send full
article text; replace the grounding check with a deterministic matcher.

**Why.** The verifier's first job is confirming that every player and injury
claim traces to a source. It was shown only titles — and player names live in
article bodies, not headlines. An LLM asked to audit for hallucinations without
the evidence does not say "I cannot tell"; it says "hallucination". On the
Titans v Cowboys run it declared a correctly sourced Cowboys injury list
fabricated, and the recalibration loop dutifully replaced that fact with a
tipster's opinion. The verifier made the run worse than no verifier at all.

The same run also showed the judge inverting two directions: it read an injury
table's "expected return: Round 23" column as *out* when it means *back*, and
cited home-favouring SHAP drivers as reasons the away side would win. Neither is
an invented fact, so "do not invent facts" never applied to them — which is why
both prompts now address direction explicitly.

The SHAP half also got a code fix rather than only a prompt one. The math tool
returns `positive_drivers` / `negative_drivers`, where positive means *raises
P(home win)*; an LLM reads positive as "agrees with me", and those two meanings
diverge whenever the model picks the away side. `label_shap_drivers()` renames
the groups after the club they favour before either LLM sees them, so the
ambiguity is gone rather than argued about. The tool's own output is unchanged —
the relabelling happens in the agent, which is the component with the problem.

The generalisable lesson, and the second instance of it after DD-31: before
trusting any LLM-based check, verify the evidence it needs is actually in its
context. Both failures were invisible in the final answer and only showed up in
the ledger. Details: `agent/adrs/0008-verifier-sees-the-evidence.md`.

## DD-34: Reddit is off by default, on evidence rather than principle

**Decision.** The r/nrl channel no longer runs unless explicitly asked for
(`include_reddit=True`, or `--reddit` on the research CLI).

**Alternatives.** Keep it always-on; delete the channel entirely.

**Why.** Measured, not assumed. Reddit's `search.rss` endpoint returns HTTP 429
to unauthenticated clients on essentially every request, and `/r/nrl/new/.rss`
rate-limits after a couple of calls. Even when the listing succeeds, the 25
newest posts rarely mention a given fixture, so the channel contributed zero
usable items across repeated Titans v Cowboys tests while costing up to 17
seconds of retry backoff. It is also the lowest-reliability tier in the tool
("treat as rumour unless corroborated") and the research gate never counted it.

The code is kept rather than deleted, because the channel works when Reddit
lets it through and the negative result is worth recording. Two fixes went in
alongside: the channel now also searches for each club instead of only reading
the newest posts, and its filter keeps recurring availability threads such as
"Team List Tuesday" that name no club in the title. Neither was enough to
justify running it by default.

## DD-35: Re-tuned for 61 features, kept despite a negligible gain

**Decision.** Hyperparameters were re-tuned with Optuna after the feature set
grew from 49 to 61 columns, and the new parameters shipped.

**Result.** Over 12 seeds on the untouched holdout: log loss 0.6501 → 0.6487,
Brier 0.2288 → 0.2284, AUC 0.6556 → 0.6558, accuracy 63.1% → 63.0%.

**Why keep it.** The gain is real on the tuning objective (log loss) but
smaller than seed noise on AUC, and accuracy moved the wrong way by one tenth
of a point. On the numbers alone this is a coin toss. It ships because
parameters tuned on the feature set actually in production are the defensible
default, not because the holdout demanded it — and recording that distinction
matters more than the 0.0013.

The wider lesson is in `Limitations.md`: at this dataset size, hyperparameter
search has stopped being where the accuracy is. A learning curve over
2021→2015 training windows is flat to within noise, so more history will not
help either. Only new signal — team lineup strength above all — would.

## DD-36: One project-root config file for model selection

**Decision.** `config.toml` at the repo root holds provider, model, timeouts
and loop caps, with a preset block per provider (ollama, openai, anthropic,
gemini, bedrock). Secrets stay in `agent/.env`. Precedence runs defaults <
`config.toml` < `.env` < environment variables, and `--provider` / `--model`
override for a single run.

**Alternatives.** Keep everything in `agent/.env`; a Python settings module;
per-tool config files.

**Why.** Switching from local Ollama to a hosted model was previously an edit
to a git-ignored dotfile that no reviewer could see and no reader could find.
Making it a committed, commented TOML at the root means the model choice is
part of the documented design rather than local machine state, and switching
providers is one line. Selecting a provider also pulls that provider's model
and region from its preset, so `--provider bedrock` cannot silently leave the
previous provider's model string in place.

Credentials are checked before the run starts (`missing_credentials`), because
discovering a missing API key ten minutes into a judgement call is a poor use
of a Friday evening. `--show-config` prints exactly what is in effect, secrets
redacted, which is the only reliable way to answer "which model did that run
actually use" for a config with four layers.

## DD-37: A club nickname is not evidence of a sport

**Decision.** An article only counts as fixture-relevant if something about it
says *rugby league* — a league marker in its text, `nrl`/`rugby-league` in its
URL path, or official provenance — not merely because a fixture nickname
appears in it.

**Why.** A Titans v Cowboys run kept fifteen articles, three of which were not
about rugby league: a Tennessee Titans backup quarterback in the *Arkansas
Democrat-Gazette*, and an actor from *Remember the Titans* discussing weight-loss
drugs. Both matched on the word "Titans" and nothing else.

The existing defence was a keyword list of foreign-sport terms (`nfl`, `nba`,
`dallas cowboys`). That is the wrong shape of rule: it enumerates what to
exclude, so every unanticipated collision gets through, and neither of these
headlines contained a listed term. Inverting it — require positive evidence of
the right sport rather than absence of evidence for a wrong one — is bounded by
what we are looking for instead of by the size of the world.

Roughly half the NRL's nicknames are shared with clubs in other codes (Titans,
Cowboys, Panthers, Raiders, Broncos, Warriors, Knights, Giants), so this is a
structural property of the domain rather than an unlucky week.

**Cost.** An article whose title, snippet and URL are all silent about the code
is deferred rather than dropped, and is judged again after its body is fetched
(DD-28). The failure mode is therefore a wasted fetch, not a lost article. A
genuine league piece would have to omit "NRL" and "rugby league" from its
headline, its summary, its URL *and* its body to be lost, which no article in
any run so far has done.
