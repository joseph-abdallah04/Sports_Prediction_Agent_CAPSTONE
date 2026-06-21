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
form. Ours is `mathematical_engine/data_lake/` — 2,324 match JSON files
exactly as nrl.com served them. Keeping the raw form means we can always
re-derive everything else if we change our minds about transformations.

**Feature store.** Where the *transformed*, model-ready data lives —
`mathematical_engine/feature_store/`. Separate from the data lake so raw
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
