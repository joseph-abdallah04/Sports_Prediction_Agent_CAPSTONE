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
Mathematical Engine is built around (see `mathematical_engine/Overview.md`).

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
Details: `mathematical_engine/feature_engineering/Architecture.md`.

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

## DD-09: Hardcoded venue-to-state dictionary for the travel flag

**Decision.** `VENUE_TO_STATE` in `flatten.py` maps all 66 venue names
(including legacy/sponsor renames) to states/countries; unknown venues
default to no-travel and print a warning.

**Alternatives.** Geocoding API; deriving from venueCity at runtime.

**Why.** 66 fixed venues do not justify a runtime dependency. Each entry
was verified once against the payload's own `venueCity` field, then
frozen as explicit, reviewable code. Validated empirically: Storm/Raiders
trigger 100% (only VIC/ACT clubs), Warriors 96%, Sydney clubs 36-47%.

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

**Decision.** `data_lake/` and `feature_store/` are gitignored.

**Why.** 313 MB of regenerable artifacts don't belong in version control;
code, configuration, and documentation do. Everything in those folders is
reproducible from the pipelines (`backfill.py`, `build_dataset.py`).
