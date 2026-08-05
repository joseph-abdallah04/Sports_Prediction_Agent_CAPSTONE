# Glossary

Plain-language definitions of the machine learning and data engineering
terms used throughout this project, with notes on how each applies here.

## The data side

**ETL (Extract, Transform, Load).** The general pattern of pulling data
from a source (extracting match JSON from nrl.com), reshaping it
(transforming nested JSON into flat tables), and storing it somewhere
useful (loading into Parquet files). Our backfill and weekly pipelines are
both ETL jobs.

**Data lake.** A storage area holding raw, untouched data in its original
form. Ours is `tools/mathematical_engine/data_lake/` — 2,324 match JSON files
exactly as nrl.com served them. Keeping the raw form means we can always
re-derive everything else if we change our minds about transformations.

**Feature store.** Where the *transformed*, model-ready data lives —
`tools/mathematical_engine/feature_store/`. Separate from the data lake so raw
facts and derived features never get mixed up.

**Parquet.** A file format for tables (like CSV, but compressed, faster,
and type-safe — a number column can never silently turn into text).
Standard in data engineering; pandas reads/writes it natively.

**Flattening.** Converting nested, hierarchical data (JSON with objects
inside arrays inside objects) into a flat table of rows and columns that
a model can consume. Stage 1 of our pipeline.

**NaN ("Not a Number") / missing value.** A cell with no value. In this
project missingness is *meaningful* (e.g. completion rate simply wasn't
recorded before 2019), so we keep NaNs rather than filling them in.

**Imputation.** Filling missing values with guesses (column averages,
etc.). We deliberately do NOT do this — XGBoost handles missing values
natively, and imputing would inject invented information. We call this
our "NaN rule".

## The modelling side

**Feature.** One input column the model uses to make predictions —
e.g. `elo_diff` (Elo rating difference) or `ctx_rest_days_diff` (rest-day
difference). Our training dataset has 49 of them. Building good features
from raw data ("feature engineering") is usually where prediction quality
is won or lost.

**Label (or target).** The answer column the model learns to predict.
Ours is `home_win`: 1 if the home team won, 0 if it lost.

**Binary classification.** Predicting one of exactly two outcomes (home
win / home loss). This is why we excluded draws from the dataset.

**Training set / test set.** The data the model learns from versus the
data used to grade it. The test set must stay hidden during training,
otherwise grading is meaningless — like marking an exam the student has
already seen.

**Chronological (time-based) split.** Splitting train/test by date rather
than randomly: we train on 2015-2023 and test on 2024-2026. This mirrors
real usage (predict the future from the past). A random split would let
the model peek at matches that happened *after* its test matches.

**Data leakage.** Any situation where information from the future (or
from the answer itself) sneaks into the features. Leakage produces models
that look brilliant in testing and fail in the real world. Our pipeline's
central design rule is that every feature uses only matches finished
*before* kickoff — and we verified this with explicit checks.

**Baseline.** The dumbest reasonable strategy, used as a floor to measure
real skill. Ours is "always pick the home team", which scores 56.9% on
the test set because home teams win that often. A model is only useful to
the extent it beats the baseline.

**Accuracy.** Of all the model's yes/no predictions, the percentage that
were correct. Our smoke test scored 62.7% — meaning ~334 correct calls
out of 533 unseen matches, +5.8 points over the baseline.

**AUC (Area Under the ROC Curve).** Grades the model's *probabilities*
rather than its final calls: if you ranked all matches by the model's
confidence in a home win, AUC is the chance that a randomly chosen actual
home-win ranks above a randomly chosen actual home-loss. 0.5 = useless
coin flip, 1.0 = perfect ranking. Ours is 0.63. We also use "univariate
AUC" in the Feature Dictionary — the AUC of a single feature used alone,
to measure its standalone predictive power.

**Calibration.** Whether predicted probabilities mean what they say: of
all matches given "70% home win", roughly 70% should actually be home
wins. Important for us because the LLM Orchestrator will reason with the
probability itself, not just the pick. Proper calibration is a Phase 3
task.

**Overfitting.** When a model memorises quirks of its training data
instead of learning general patterns — great training scores, poor
real-world scores. Guarded against with held-out test sets and
sensible model complexity.

**Hyperparameters / tuning.** The dials on the learning algorithm itself
(number of trees, tree depth, learning rate...). "Tuning" is searching
for the dial settings that generalise best. Our smoke test used
near-default settings on purpose; tuning happens in Phase 3.

**Decision tree.** A model that predicts by asking a sequence of
yes/no questions about the features ("Is elo_diff > 40? Is rest_days_diff
< -2?...") and giving an answer at the leaf.

**Gradient boosting / XGBoost.** A technique that builds hundreds of small
decision trees *in sequence*, each new tree correcting the errors of the
ones before, then sums their votes. XGBoost is the most widely used
implementation — the industry standard for tabular (rows-and-columns)
data, and typically beats neural networks on datasets of our size
(~2,300 rows).

**Smoke test.** A quick, deliberately simple end-to-end check that
something basically works before investing in the full version. Ours
trained a near-default XGBoost purely to confirm the dataset is learnable
and leak-free — it is not the final model.

**SHAP (SHapley Additive exPlanations).** A method that, for any single
prediction, fairly attributes how much each feature pushed the probability
up or down (based on Shapley values from game theory). This is how the
mathematical engine will explain *why* it predicts a 74% home win, so the
LLM Orchestrator receives reasoning instead of a black-box number.
Phase 3.

## The ratings and features side

**Elo rating.** A self-correcting strength score (from chess). Winners
take points from losers; beating a strong team earns more than beating a
weak one; the size of every exchange depends on how surprising the result
was. Our strongest feature.

**Mean reversion (off-season).** Each new season we pull every team's Elo
30% of the way back toward average, reflecting roster changes — last
year's juggernaut usually starts strong-but-less-dominant, not identical.

**Bradley-Terry model.** A statistical model that assumes each team has a
hidden strength number and the probability A beats B is
`strength_A / (strength_A + strength_B)`. It refits all strengths jointly
from the entire match history (recent matches weighted more), capturing
chains of evidence like "A beat B, who beat C".

**Pythagorean expectation.** Estimates the win rate a team *deserves*
from its points scored vs conceded (`PF^2.5 / (PF^2.5 + PA^2.5)`).
Points margin predicts future wins better than past wins do, because
close-game results are heavily luck.

**Rolling window / rolling average.** An average over only the last N
observations (e.g. average post-contact metres over the previous 5 games),
recomputed as the window slides forward. Captures *current* form rather
than all-time tendencies. The "shift" in our code excludes the current
match from its own window — that is the anti-leakage trick.

**Differential (`_diff`).** Home value minus away value. We feed the model
contrasts ("home has 110 more Elo points") rather than two absolutes,
because the matchup gap is the signal.

**Proxy feature.** A stand-in measured quantity used when the thing you
actually want isn't in the data — e.g. our `support_plays` proxy
(line-break assists + try assists) because the NRL payload has no direct
"support runs" stat. Proxies are honest as long as they're documented.

**Home-ground advantage (HGA).** The empirical tendency of home teams to
win more often (56.3% in our data). We model it per-venue with smoothing,
rather than as a single yes/no flag.

**Smoothing (Beta/prior).** When estimating a rate from few observations
(home-win rate at a venue with 4 recorded games), blend it with a prior
assumption (55%) so small samples can't produce wild values. The prior's
influence fades as real observations accumulate.

## Phase 3 terms (model, tuning, calibration)

**Hyperparameter.** A setting of the *learning process itself* that isn't
learned from the data and must be chosen in advance — e.g. how many trees to
build, how deep each tree can grow, the learning rate. Contrast with model
*parameters* (the split thresholds inside the trees), which training learns.

**Hyperparameter tuning.** Systematically trying combinations of
hyperparameters and keeping the set that scores best on held-out data.

**Optuna.** The library we use to automate tuning. We define the search
space, the scoring function, and the trial budget once; Optuna intelligently
decides which combinations to try next (focusing on promising regions). "We
build the exam; Optuna sits it 200 times."

**TPE (Tree-structured Parzen Estimator).** Optuna's default search strategy.
It models which regions of the search space tend to score well and samples
new trials from there, rather than searching blindly.

**Objective function.** The single number a tuner tries to minimise (or
maximise). Ours is mean log loss across the validation folds.

**Log loss (logistic / cross-entropy loss).** A score for *probabilistic*
predictions: it punishes confident wrong answers harshly and rewards
confident right ones. Lower is better. It is a "proper scoring rule", meaning
it is optimised only by reporting your true probabilities — which is why we
tune on it rather than accuracy. A coin-flip (always 0.5) scores ~0.693;
predicting the base rate scores ~0.687 here.

**Brier score.** The mean squared error between predicted probabilities and
outcomes (0/1). Like log loss it measures probability quality, but penalises
errors less severely. Lower is better; we use it to compare calibration
methods.

**Calibration.** Adjusting a model's probabilities so they mean what they
say — if it outputs 0.70 across many games, the home team should win about
70% of them. Raw tree-ensemble probabilities are often mis-scaled.

**Platt scaling (sigmoid calibration).** A calibration method that fits a
logistic (S-shaped) curve mapping raw scores to calibrated probabilities.
Robust with limited data; our default.

**Isotonic regression.** A calibration method that fits a free
(non-parametric) increasing step function. More flexible than Platt but needs
more data and can overfit small calibration sets.

**Calibration curve (reliability diagram).** A plot of predicted probability
(x) vs observed frequency (y). A perfectly calibrated model lies on the
diagonal.

**Expanding-window validation.** A time-aware cross-validation where each
fold trains on all seasons before a target season and validates on that
season — then the window expands to include it for the next fold. Prevents
the model from "seeing the future".

**Holdout set.** Data deliberately set aside and never used during tuning or
calibration, reserved to estimate real future performance (ours: 2025-2026).

**Out-of-time (OOF) predictions.** Predictions made on data the model did not
train on, generated via the validation folds. We fit the calibrator on these
so calibration generalises rather than memorising the training set.

**SHAP (SHapley Additive exPlanations).** A method, grounded in cooperative
game theory, that attributes a single prediction across its input features —
how much each feature pushed the prediction up or down, and in which
direction. It is what turns the model from a black box into the reasoning
payload the LLM Orchestrator consumes.

**Model artifact.** A saved output of training that can be reloaded to make
predictions without retraining — here the booster (`model.ubj`), the
calibrator (`calibrator.pkl`), and the feature/metadata files in `models/`.

**Parity test (train/serve consistency).** A check that features built for a
*future* fixture via the inference path exactly equal the features the model
trained on for the same (historical) match. Guards against "train/serve
skew", where a model is fed differently-computed features in production than
in training.

**Baseline.** A trivial reference a real model must beat — e.g.
always-pick-home accuracy (55.8%) or always-predict-the-base-rate log loss
(0.687). Beating the baseline is the minimum bar for "the model learned
something".

**AUC (Area Under the ROC Curve).** Defined in the metrics section above; in
Phase 3 it is unchanged by calibration because calibration is monotonic (it
re-labels probabilities without reordering matches).

## The agent side

**LLM (Large Language Model).** A model that predicts the next chunk of text
given the text so far. Ours reads tool outputs and writes a prediction in
words. It knows nothing about this weekend's NRL beyond what we put in front
of it, which is why every fact reaches it through a tool.

**Agent.** A program that lets an LLM take actions (call tools) rather than
only produce text. Ours is deliberately a *constrained* agent: the code decides
which tools run and in what order, and the LLM supplies judgement at fixed
points (DD-22).

**ReAct (Reason + Act).** The common agent pattern where the LLM freely decides
its next tool call in a loop until it declares itself finished. We rejected it
for this project — see the Orchestrator ADR 0001 — because a marking rubric
needs a reproducible trace, not a different tool sequence every run.

**Tool call.** A structured function invocation with typed arguments and a
JSON result — here `set_fixture_scene`, `research_fixture_news`, and
`predict_match`. Tools return *facts only*; none of them picks a winner.

**MCP (Model Context Protocol).** An open standard for exposing tools to LLM
clients, so the same three tools work from our own orchestrator and from an
external client like Claude Desktop without being rewritten.

**Prompt (system / user).** The instructions and data given to the LLM for one
call. The system prompt sets the role and the rules; the user prompt carries
the payload. Our prompts live in `agent/src/agent_app/prompts/`.

**Temperature.** How much randomness the LLM is allowed when choosing words.
Near 0 gives repeatable, conservative output; we run judgement at 0.2 and the
verifier at 0.1 because we want consistency, not creativity.

**Context window.** The maximum amount of text an LLM can consider at once.
Everything must fit — which is why the ledger is abridged before being sent to
the verifier, and why *what we cut out* turned out to matter (ADR 0008).

**Hallucination.** An LLM stating something specific and plausible that is not
true and not in its inputs. The defence here is architectural: facts arrive
only via tools, and the verifier checks each claim back against the tool output
that supposedly supports it.

**Grounding.** Requiring a claim to trace to a specific piece of supplied
evidence. "The Cowboys are missing Bateman" is grounded only if an article in
the ledger says so.

**Ledger.** The full JSON record of one run — every tool request and response,
every LLM step, both loops, and the final judgement — written to
`agent_runs/fixtures/<fixture>/<run>/ledger.json`. It is what makes the agent
auditable rather than merely plausible, and both bugs found in ADR 0006 and
ADR 0008 were invisible in the answer and obvious in the ledger.

**Orchestrator.** The code that runs the fixed six-stage sequence: scene →
query plan → research ∥ math → judgement → verifier → done.

**Research gate.** A coded (non-LLM) check on whether the research results are
good enough to reason from: enough items with body text, at least one official
or availability source, and not every wide-net channel failing empty.

**Verifier.** A second LLM pass that audits the judgement against the ledger
and can send it back once for recalibration. It cannot call tools — its job is
to check reasoning, not to gather more evidence.

**Recalibration loop.** The single permitted re-judge after the verifier
objects, run in the same session with no new tool calls (ADR 0004).

**Confidence anchoring.** Requiring the LLM's stated confidence to stay within a
set distance of the calibrated model probability. This system used to do it and
deliberately no longer does: anchoring makes the agent's Brier score a
restatement of the model's, so the comparative evaluation cannot tell them apart
whatever the system actually does (DD-41). Confidence is now the agent's own
number, kept honest by prompt-level bands rather than by the model.

**Circular evaluation.** Measuring a system with a metric its own design forces
to a particular answer. The anchored-confidence case is the example this project
had to fix: the Brier comparison would have reported "no difference" as a finding
when it was a property of the prompt.

**Record file.** `record.json`, written beside each ledger — a small flat
projection of the run's numbers so a write-up does not require reading several
hundred lines of ledger to find a confidence score (ADR 0010).

**Running log.** `agent_runs/predictions_log.csv`, one appended row per
prediction ever made, ending in columns the agent never writes so the manual half
of the evaluation lives in the same table (ADR 0010).
