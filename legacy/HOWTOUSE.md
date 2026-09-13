# How to use this

A practical guide to running the agent and finding everything it produces.
Written for someone who has not run it before and needs to be running it
reliably for the testing window.

Every command below is copy-pasteable. Every file path is real. If something
here disagrees with what you see on your machine, the machine is right and this
document is stale — tell me.

**Contents**

1. [One-time setup](#1-one-time-setup)
2. [The 30-second check before any real run](#2-the-30-second-check-before-any-real-run)
3. [Predicting one game](#3-predicting-one-game)
4. [Predicting a whole round](#4-predicting-a-whole-round)
5. [Scoring the round after the games](#5-scoring-the-round-after-the-games)
6. [Where everything is stored](#6-where-everything-is-stored)
7. [Everything the agent records](#7-everything-the-agent-records)
8. [Every metric, and what it means](#8-every-metric-and-what-it-means)
9. [Full command and flag reference](#9-full-command-and-flag-reference)
10. [When something goes wrong](#10-when-something-goes-wrong)

---

## 1. One-time setup

You only do this once. Roughly five minutes, plus however long the model pull
takes.

```bash
cd /Users/josephabdallah/Coding/UniversityProjects/Capstone/Sports_Prediction_Agent_CAPSTONE

# Install the agent's dependencies (also installs the three fact tools)
cd agent
uv sync
```

The agent talks to a local LLM by default, so Ollama has to be running with the
model pulled:

```bash
ollama pull gemma4:31b-mlx # Apple Silicon MLX build; ~18 GB, one time
ollama serve               # leave this running in its own terminal
```

You do **not** need to create or edit `.env` for local running. Provider and
model live in [`config.toml`](config.toml) at the repo root, which is already
set to Ollama and `gemma4:31b-mlx`.

Confirm the whole thing is wired up:

```bash
cd agent
uv run python -m agent_app.cli --show-config
```

```
config file      /…/Sports_Prediction_Agent_CAPSTONE/config.toml
provider         ollama
model            gemma4:31b-mlx
litellm model id ollama/gemma4:31b-mlx
timeout          600s, 2 retries
verifier         on
loops            research<=1, verifier<=1, queries<=6
runs dir         /…/Sports_Prediction_Agent_CAPSTONE/agent_runs
credentials      openai=- anthropic=- gemini=- aws_region=-
```

`credentials  …=-` just means no API keys are set, which is correct for local
Ollama. The 600s timeout is deliberate: Gemma 4 with thinking enabled emits a
scratchpad before the JSON, and the verifier packs eight checks into a large
abridged ledger.

> **All agent commands run from the `agent/` directory.** If you get
> `No module named agent_app`, you are in the wrong folder.

---

## 2. The 30-second check before any real run

Run this before every round. It takes about two seconds and needs no network and
no LLM:

```bash
cd agent
uv run python scripts/smoke_orchestrator.py
```

It runs the entire control loop with the fact tools and the LLM replaced by
stubs, and asserts dozens of properties about what came out — every stage
executed, both output files written, the verifier recorded its eight checks,
the round harness appends instead of overwriting. You want the last line to
read:

```
SMOKE_OK
```

If it does not, **stop and fix that before spending an hour of inference.** This
exists because a one-character mistake once crashed a real run eleven minutes in,
at the second-to-last stage.

To also confirm the three fact tools can still reach the outside world (nrl.com,
the news channels, the trained model), which takes about two minutes:

```bash
cd tools/mcp_gateway
uv run python scripts/smoke_tools.py     # want: SMOKE_OK
```

---

## 3. Predicting one game

```bash
cd agent
uv run python -m agent_app.cli --home Titans --away Cowboys --round 23
```

`--home` must be the side actually listed at home on the draw, and both names
must be official NRL nickNames (`Titans`, `Wests Tigers`, `Sea Eagles`, …). The
full list is in the [root README](README.md#official-nrl-nicknames). Get the
pairing or the order wrong and it stops in a few seconds and tells you the
round's real fixtures:

```
No fixture found for Broncos v Storm in season 2026 round 23. Round 23 is:
Titans v Cowboys, Warriors v Panthers, Roosters v Bulldogs, Storm v Sea Eagles,
Dolphins v Broncos, Rabbitohs v Eels, Raiders v Knights, Dragons v Sharks
```

`--round` is optional — without it the agent finds the next upcoming meeting of
those two teams. Passing it is safer, because it fails fast instead of
predicting a fixture you did not mean.

### What you will see while it runs

Expect **8–15 minutes** on local Ollama. It is not hung; the judgement and
verifier calls each take about three to five minutes. **Run one fixture at a
time** — two concurrent `gemma4:31b-mlx` pipelines on a 48 GB machine thrash memory
and often time out the verifier. The terminal reports each stage:

```
[1/6] Scene: fixture, venue, weather
[2/6] Query plan: LLM writes research queries
[3/6] Research + math (parallel)
Research gate: ok=True (items_with_body=8 official/nrl=True availability=True)
Research refine loop: skipped (gate passed or disabled)
[4/6] Judgement: LLM synthesises scene + research + math
LLM responded in 230.2s (810 chars)
Judgement OK in 230.2s: winner=home confidence=0.54
  factor [math] Pythagorean form (last 10) shows an +11% expected-win gap…
  factor [research] The Cowboys suffered a record 82-12 defeat in Round 22…
[5/6] Verifier: checklist + LLM audit
Checklist: pass=True issues=[]
LLM audit: pass=True issues=[] instruction=''
  check sourced_claims           pass   Matched Bateman/Mahoney return to Zero Tackle…
  check availability_direction   pass   Source lists expected return in Round 23…
  check shap_attribution         pass   Elo correctly attributed to the Cowboys…
  check weather_not_headline     pass   Weather is not mentioned as a key factor.
  check research_used            pass   Key factors identify Zero Tackle and NRL.com.
  check confidence_justified     pass   Summary explains 0.54; inside the 0.55-0.65 band.
  check driver_proportionality   pass   Relies on Elo, a top SHAP driver.
  check omitted_math_signals     pass   Top drivers on both sides acknowledged in factors/summary.
Verifier recalibrate: skipped (audit/checklist passed)
[6/6] Done
=== Final: winner=home confidence=0.54 | total 615.3s ===
  ledger  agent_runs/fixtures/2026-R23_Titans-v-Cowboys/20260803T132405Z/ledger.json
  summary agent_runs/fixtures/2026-R23_Titans-v-Cowboys/20260803T132405Z/summary.md
  thinking agent_runs/fixtures/2026-R23_Titans-v-Cowboys/20260803T132405Z/thinking.md
  record  agent_runs/fixtures/2026-R23_Titans-v-Cowboys/20260803T132405Z/record.json
  log     agent_runs/predictions_log.csv
```

The query planner always asks for an **odds / favourite** search as well as
availability and preview. Prices that survive in article excerpts are
regex-lifted into a `market_mentions` block for the judge — acknowledge the
market, do not copy it.

The scene tool also scrapes the official [NRL ladder](https://www.nrl.com/ladder/)
into a `standings` block (position, W-D-L, PF/PA, points difference). That
reaches the judge and appears in `summary.md`, so ladder SHAP drivers can be
checked against readable numbers (e.g. Titans PD −122 vs Cowboys −98).

Then it prints a JSON summary and exits `0`. Exit code `1` means the run failed,
`2` means a configuration problem (missing API key) and it never started.

### Where the output went

The last four lines of the terminal output give you every path:

```
agent_runs/
├── fixtures/2026-R23_Titans-v-Cowboys/20260803T132405Z/
│   ├── summary.md      ← read this first: what it predicted and why
│   ├── thinking.md     ← the model's real scratchpad (when the provider returns one)
│   ├── record.json     ← the numbers for your calculations
│   └── ledger.json     ← everything, unabridged
└── predictions_log.csv ← one row appended per prediction, ever
```

---

## 4. Predicting a whole round

An NRL round runs Thursday to Sunday. Round 23 for example:

| Day | Fixtures | Kickoff (AEST) |
| --- | --- | --- |
| Thu 6 Aug | Titans v Cowboys | 19:50 |
| Fri 7 Aug | Warriors v Panthers, Roosters v Bulldogs | 18:00, 20:00 |
| Sat 8 Aug | Storm v Sea Eagles, Dolphins v Broncos, Rabbitohs v Eels | 15:00, 17:30, 19:35 |
| Sun 9 Aug | Raiders v Knights, Dragons v Sharks | 14:00, 16:05 |

**Step 1 — see what is still ahead of kickoff.** Two seconds, no LLM:

```bash
cd agent
uv run python -m agent_app.harness run --season 2026 --round 23 --dry-run
```

```
Fixture                    Kickoff                    In  Status
Titans v Cowboys           Thu 06 Aug 19:50          68h  would predict now
Warriors v Panthers        Fri 07 Aug 18:00          91h  would predict now
…
```

**Step 2 — predict, one match day at a time.** The harness is incremental: it
appends to the predictions file, skips fixtures it has already done, and
*refuses* to predict a fixture whose kickoff has passed. So you can wait for
each day's team lists without damaging the earlier records:

```bash
# Wednesday night — just Thursday's game (~10 min)
uv run python -m agent_app.harness run --season 2026 --round 23 --only Titans

# Friday, finished before 18:00 — picks up the two Friday games (~20 min)
uv run python -m agent_app.harness run --season 2026 --round 23

# Saturday, finished before 15:00 — the three Saturday games (~30 min)
uv run python -m agent_app.harness run --season 2026 --round 23

# Sunday, finished before 14:00 — the last two (~20 min)
uv run python -m agent_app.harness run --season 2026 --round 23
```

Note the plain `run` on Friday: it works out for itself that Thursday's game is
already predicted and Friday's two are not. `--only` is only needed when you
want *fewer* fixtures than that.

Budget **8–15 minutes per fixture** on local Ollama, and keep fixtures
sequential (one process at a time). The run must *finish* before kickoff to
count, so start with room to spare.

Everything lands in one place per round:

```
agent_runs/rounds/2026-R23/predictions.json
```

Each fixture in that file also points at its own full ledger under
`agent_runs/fixtures/`, so nothing is summarised away.

---

## 5. Scoring the round after the games

After the last game has finished:

```bash
cd agent
uv run python -m agent_app.harness score --season 2026 --round 23
```

This reads back `predictions.json` — written before the games — fetches the
actual results from nrl.com, and scores three predictors against each other:
the agent, the raw maths model, and always backing the home team.

```
=== Season 2026, round 23 ===
Scored 8 fixtures (0 not finished, 0 draws excluded)

fixture                        actual             agent    math
Titans v Cowboys                 18-24       away 0.55  OK     0.51
…

predictor        n  accuracy    brier  log_loss
agent            8     0.625   0.2410    0.6712
math             8     0.625   0.2388    0.6689
```

It writes two more files beside the predictions:

```
agent_runs/rounds/2026-R23/
├── predictions.json    what was predicted, before kickoff
├── scored.json         the same plus results and all metrics
└── summary.md          the scorecard, readable
```

Because predicting and scoring are separate commands, and a played fixture is
refused rather than predicted, the numbers cannot be back-fitted. That property
is the whole reason the harness exists.

---

## 6. Where everything is stored

```
Sports_Prediction_Agent_CAPSTONE/
│
├── config.toml                      ← the only file you edit to change models
│
├── agent_runs/                      ← EVERYTHING THE AGENT PRODUCES
│   ├── README.md                    layout notes (committed)
│   ├── predictions_log.csv          ← EVERY prediction ever, one row each
│   ├── fixtures/
│   │   └── 2026-R23_Titans-v-Cowboys/       one folder per fixture
│   │       ├── 20260803T100112Z/            one folder per run of it
│   │       │   ├── summary.md               ← start here
│   │       │   ├── thinking.md              ← model scratchpad (real thinking)
│   │       │   ├── record.json              ← the numbers, extracted
│   │       │   └── ledger.json              ← the complete record
│   │       └── 20260806T090500Z/            a later run of the same game
│   ├── rounds/
│   │   └── 2026-R23/
│   │       ├── predictions.json     written BEFORE kickoff
│   │       ├── scored.json          written AFTER the games
│   │       └── summary.md           the scorecard
│   └── archive/                     runs from before this layout
│
├── tools/qualitative_research/
│   ├── cache/<key>.json             every article kept, per fixture per day
│   └── debug/dropped/<key>.json     every article DROPPED, with the reason
│
├── tools/fixture_scene/
│   └── cache/<key>.json             draw, venue and weather payloads
│
└── tools/mathematical_engine/reports/
    ├── holdout_metrics.json         model accuracy on 376 unseen matches
    ├── calibration_curve.png        predicted vs actual probability
    └── shap_summary.png             which features matter, globally
```

Multiple runs of the same fixture sit side by side, timestamped, which is how
you compare a Monday prediction against one made after Thursday's team lists.

`agent_runs/` is git-ignored — it is results, not source — so nothing you
generate will show up in a commit.

### Which file answers which question

| Question | File |
| --- | --- |
| **The numbers, for my own calculations** | **`predictions_log.csv`** |
| The numbers for one run, without the CSV | `fixtures/<fixture>/<run>/record.json` |
| What did it predict, and why? | `fixtures/<fixture>/<run>/summary.md` |
| What was the model *thinking*? | `fixtures/<fixture>/<run>/thinking.md` |
| Exactly what did each tool return? | `fixtures/<fixture>/<run>/ledger.json` |
| What did the verifier actually check? | `summary.md`, section "What the verifier checked" |
| How long did each stage take? | `ledger.json` → `tool_calls[].duration_ms` |
| Which articles were thrown away, and why? | `tools/qualitative_research/debug/dropped/` |
| Did the agent beat the model this round? | `rounds/<round>/summary.md` |
| What was predicted before kickoff? | `rounds/<round>/predictions.json` |
| How good is the maths model overall? | `tools/mathematical_engine/reports/holdout_metrics.json` |

---

## 7. Everything the agent records

Four files, in increasing order of detail. Start at the top and go down only when
the level above does not answer the question.

| File | Scope | Use it for |
| --- | --- | --- |
| `predictions_log.csv` | every prediction ever made | your accuracy, reliability and Brier calculations |
| `record.json` | one run | the numbers for that run, without the ledger |
| `summary.md` | one run | reading what it decided and why |
| `thinking.md` | one run | the model's real scratchpad per LLM step (when available) |
| `ledger.json` | one run | the unabridged evidence behind any of the above |

### `predictions_log.csv` — the one you will actually use

One row per prediction, appended, at `agent_runs/predictions_log.csv`. It is
never rewritten, so it accumulates across every round of the testing window and
becomes the single table your write-up is calculated from.

The agent fills these columns:

| Column | Note |
| --- | --- |
| `run_id` | Links to the run folder |
| `predicted_at_utc`, `predicted_at_local` | When the prediction was finalised |
| `season`, `round`, `home_team`, `away_team`, `venue`, `kickoff_local` | The fixture |
| `hours_before_kickoff` | How far ahead of the game it predicted — your freshness evidence |
| `predicted_winner` | The team name, not `home`/`away` |
| `predicted_side` | `home` or `away` |
| `confidence` | The agent's confidence in **its own pick**, 0.50–0.95 |
| `agent_home_win_prob` | The same number expressed as P(home win), for Brier |
| `math_home_win_prob` | What the maths tool alone said. Independent of the agent (DD-41) |
| `math_prediction` | The tool's own pick, in words |
| `research_items_kept`, `research_queries`, `research_refine_triggered` | What the research layer did |
| `verifier_ran`, `checklist_pass`, `audit_pass`, `recalibration_triggered` | What the verification layer did |
| `confidence_before_recalibration` | Only set when the verifier sent it back |
| `llm_provider`, `llm_model`, `wall_seconds`, `failed` | Run conditions |
| `ledger_path` | Where to look when a number needs explaining |

And these are **left empty for you**, and are never touched by the agent:

`actual_winner`, `actual_home_score`, `actual_away_score`,
`vanilla_llm_winner`, `vanilla_llm_confidence`, `statsinsider_home_prob`,
`notes`

Because the file is opened in append mode, anything you type into earlier rows
survives every later run. One caveat: if a spreadsheet is holding the file open
when a run finishes, the append can fail — the run is unaffected and
`record.json` is still written, but do your working in a copy to be safe.

**Computing your metrics from it.** Accuracy per round is the share of rows in
that round where `predicted_winner == actual_winner`. Reliability is the same
calculation over every row in the window. Brier is the mean of
`(agent_home_win_prob − h)²` where `h` is 1 if the home team won and 0 if not —
which is algebraically identical to the §3.6.2 form using confidence in the
picked side, so either arrangement gives the same number. Swap in
`math_home_win_prob`, `vanilla_llm_confidence` or `statsinsider_home_prob` to
score the other systems the same way.

### `record.json` — one run, flattened

Beside each `ledger.json`. Same numbers as the CSV row plus the things that do
not fit a cell: the SHAP drivers, the research items with citable domain and
publication date, the judge's summary and key factors, and every verifier check
with its verdict and evidence. Derived from the ledger with no LLM and no
network, so it can be rebuilt from any past run.

### `ledger.json` — the complete record

Nothing is removed from it, and nothing is truncated: `summary.md`,
`record.json` and the `at_a_glance` block are all *derived* views, so every
number in them traces back to the raw tool response below.

Top-level keys, in the order they appear (summary first, detail last):

| Key | What is in it |
| --- | --- |
| `schema_version` | Ledger format version, currently `2` |
| `run_id` | `<timestamp>-<short uuid>`, unique per run |
| `at_a_glance` | Derived one-screen summary — see below |
| `created_at` / `updated_at` | UTC timestamps; the ledger is rewritten at every stage |
| `request` | What was asked: teams, season, round, question, provider, model, loop caps |
| `error` | `null` unless the run failed; otherwise the stage and detail |
| `final_judgement` | The prediction the agent settled on |
| `research_loop` | Gate diagnostics, and queries before/after any refine |
| `verifier_loop` | Checklist, LLM audit with per-check evidence, judgement before/after |
| `thinking_trace` | Raw thinking text per LLM step (same content as `thinking.md`) |
| `agent_steps` | Every LLM step in order, with its full payload |
| `tool_calls` | Every tool request and complete response, with timings |

### `at_a_glance`

The answer to "what happened" without scrolling:

```json
{
  "fixture": "Titans v Cowboys",
  "round": 23,
  "kickoff": "2026-08-06T19:50:00+10:00",
  "venue": "Cbus Super Stadium",
  "predicted_winner": "Cowboys",
  "confidence": 0.55,
  "model_home_win_probability": 0.5063,
  "model_prediction": "Home Win",
  "research_items_kept": 15,
  "research_refine_triggered": false,
  "verifier_ran": true,
  "verifier_checklist_pass": true,
  "verifier_audit_pass": true,
  "verifier_checks_reported": 8,
  "recalibrated": false,
  "llm": "ollama/gemma4:31b-mlx",
  "failed": false
}
```

### `final_judgement` — the agent's reasoning

```json
{
  "winner": "away",
  "home_team": "Titans",
  "away_team": "Cowboys",
  "confidence": 0.55,
  "summary": "While the math model slightly favours the Titans…",
  "key_factors": [
    {"source": "research", "detail": "Griffin Neame, John Bateman and Reed Mahoney are all expected to return in Round 23 (zerotackle.com)."},
    {"source": "math", "detail": "The Cowboys hold an Elo rating advantage (-129 points)…"}
  ],
  "disagreements_with_math": "Picked against the model because research shows three key Cowboys players returning…"
}
```

Every factor is tagged with where it came from (`research`, `math`, `scene`), and
when the agent picks against the maths model it has to say why in
`disagreements_with_math`.

### `agent_steps` — the LLM's actual output at each stage

One entry per LLM step, each with `step`, `at`, and the full `payload`:

| Step | What it holds |
| --- | --- |
| `query_plan` | The search queries the LLM wrote for this fixture |
| `research_refine` | Rewritten queries, if the research gate failed (usually absent) |
| `judgement` | The complete judgement JSON the LLM returned |
| `verifier_audit` | The checklist result and the LLM audit, including every check |
| `verifier_recalibrate` | Issues, instruction, and the judgement before and after |

This is where the "thinking" lives, to the extent that a language model has any:
these are its verbatim structured outputs at each decision point.

### `tool_calls` — the evidence, in full

Each entry has `call_id`, `tool_name`, `started_at`, `finished_at`,
`duration_ms`, `request`, `response`, `error`. Three tools are always called:

**`set_fixture_scene`** — `fixture` (teams, kickoff, venue, city, season, round,
match-centre URL), `weather` (forecast plus the `math_weather_label` fed to the
model), `sources` (every URL used), `cache_hit`, `tool_version`.

**`research_fixture_news`** — `items` (every article kept), `queries_run`,
`channels` (per-channel status and count), `filter_summary`, `cache_hit`. Each
article carries:

| Field | Meaning |
| --- | --- |
| `title`, `url`, `snippet` | As published |
| `body_excerpt` | The article text the LLM actually read |
| `channel` | `nrl_news`, `google_news_rss`, `duckduckgo` |
| `source_tier` | `official`, `media`, `unverified_community` |
| `published_at`, `age_hours` | When it was published, and how old at run time |
| `relevance_score` | Ranking score from the filter |
| `keep_reasons` | Why the filter kept it — e.g. `mentions_both_teams`, `promoted_after_body_fetch` |
| `reliability`, `guidance` | How much weight the judge is told to give it |

`filter_summary` accounts for every article that was *not* kept:

```json
{"dropped_stale": 83, "dropped_wrong_round": 7, "dropped_noise": 12,
 "dropped_irrelevant": 20, "kept": 8, "deferred_pending_body": 40,
 "promoted_after_body": 5, "dropped_no_body": 4}
```

The dropped articles themselves — title, URL, and the specific rule that
rejected each one — are in `tools/qualitative_research/debug/dropped/<key>.json`.
That is the file to open when you suspect something relevant was thrown away.

**`predict_match`** — `home_win_probability` (calibrated), `prediction`,
`probability`, `shap_explanations`, and the `fixture` the features were built
for. SHAP drivers are grouped by the club they favour, so
`favouring_Titans_home_win` and `favouring_Cowboys_away_win` rather than an
ambiguous "positive" and "negative".

### `verifier_loop` — the audit trail

```json
{
  "verifier_ran": true,
  "recalibration_triggered": false,
  "checklist": {"pass": true, "issues": []},
  "llm_audit": {
    "ran": true, "pass": true, "issues": [], "instruction": "",
    "checks": [
      {"check": "sourced_claims", "verdict": "pass",
       "evidence": "Matched Bateman/Mahoney return to Zero Tackle…"}
    ]
  },
  "judgement_before": { … },
  "judgement_after": null
}
```

Two separate flags, because they answer different questions. **`verifier_ran`**
means the checks happened. **`recalibration_triggered`** means they sent the
judgement back to be redone. A healthy run is `true` then `false` — the verifier
looked and found nothing to fix. That is not a skipped verifier.

`judgement_after` is `null` when no recalibration was needed. When one happens,
both versions are kept so you can see exactly what changed and why. Recalibration
asks the judge to address the flagged gaps against the full evidence packet; it
may change the pick or confidence if that material actually moves the call, and
it often keeps both numbers while expanding the write-up (especially on
`omitted_math_signals`, which is coverage rather than a weight instruction).

The eight audit checks:

| Check | What it confirms |
| --- | --- |
| `sourced_claims` | Every player, injury or quote appears in an article body or scene field |
| `availability_direction` | "Expected return this round" was read as *available*, not *missing* |
| `shap_attribution` | Each SHAP driver is credited to the club whose group it sits in |
| `weather_not_headline` | Weather is not a key factor unless SHAP surfaced it (audit only — see below) |
| `research_used` | At least one key factor is sourced from research, when research found items |
| `confidence_justified` | The summary says what set the confidence, and the number suits a high-variance competition |
| `driver_proportionality` | A minor SHAP factor is not treated as decisive |
| `omitted_math_signals` | Top SHAP drivers on *both* sides are at least acknowledged — silence is the failure, not disagreeing with them |

Each returns `pass`, `fail`, `not_applicable` or `unable`, with the evidence it
matched. Structural checks (`research_used`, confidence bounds) are *also*
enforced in code by the checklist. `weather_not_headline` is audit-only: a coded
keyword scan once flagged "hamstring strain" as weather because `rain` is a
substring of `strain`, and burned a recalibration while this audit check had
already passed.

`omitted_math_signals` is the coverage half of the SHAP audit. The other SHAP
checks stop fabrication and overweighting; this one stops the judge from quietly
ignoring a driver that was in the math packet. If it fails, recalibration asks
the judge to *evaluate* the skipped signal. The verifier must not steer the pick
("travel is decisive; lower confidence"); any number change is the judge's call
after reconsidering the full packet.

Note what `confidence_justified` deliberately does **not** do: compare the
confidence to the maths probability. The agent is entitled to its own number, and
tying the two would make the agent's Brier score a restatement of the model's,
so the comparison could never show a difference (DD-41, ADR 0009). The only coded
bounds are a floor of 0.50 — below which the judge would have contradicted its
own pick — and a ceiling of 0.95.

---

## 8. Every metric, and what it means

### Per round, after scoring

In `rounds/<round>/scored.json` and `summary.md`, for the agent and the maths
model separately:

| Metric | Meaning | Better |
| --- | --- | --- |
| `n` | Fixtures actually scored (draws and unfinished games excluded) | — |
| `accuracy` | Share of games where the picked side won | higher |
| `brier` | Mean squared error of the probability — rewards being confident *and* right | lower |
| `log_loss` | Penalises confident mistakes harshly | lower |
| `home_win_rate` / `always_home_accuracy` | The baseline: what you would score by always backing the home team | — |
| `n_pending` | Fixtures not yet finished | — |
| `n_draws_excluded` | Draws, which the binary model cannot express | — |

Accuracy alone is a poor measure over eight games — one result swings it by 12
points. Brier and log loss use the whole probability, so they say more from a
small sample. All three are reported for all three predictors.

Per fixture, `scored.json` also holds `actual_score`, `margin`,
`actual_winner`, the agent's implied `agent_home_prob`, the model's
`math_home_prob`, `predicted_at`, and the path to that fixture's ledger.

### Across the whole testing window

`scored.json` is per round; there is no command that totals several rounds into
one figure. That is deliberate — the window-level numbers, and the two control
systems, are calculated by hand from `predictions_log.csv`, which already spans
every round in one table. Treat the per-round `accuracy` and `brier` above as a
cross-check on your own arithmetic rather than the source.

### The maths model overall

`tools/mathematical_engine/reports/holdout_metrics.json`, measured on 376
matches from 2025–2026 that the model never trained on:

| Predictor | Accuracy | AUC | Log loss | Brier |
| --- | --- | --- | --- | --- |
| Always back the home team | 56.6% | — | — | — |
| Base rate (0.564 every time) | — | 0.500 | 0.684 | — |
| **This model (sigmoid-calibrated)** | **62.2%** | **0.653** | **0.651** | **0.230** |

The file also carries `global_shap_top` — the features that matter most across
all matches, currently ladder points per game, Bradley-Terry strength and Elo —
plus the uncalibrated and isotonic variants for comparison.

`calibration_curve.png` is the one worth putting in the report: it shows
predicted probability against realised win rate, which is what justifies
trusting the number rather than just the pick. [`Limitations.md`](Limitations.md)
breaks accuracy down by confidence band and answers the 70% question honestly.

---

## 9. Full command and flag reference

All from `cd agent`.

### Single fixture

```bash
uv run python -m agent_app.cli --home <Home> --away <Away> [flags]
```

| Flag | Effect |
| --- | --- |
| `--home <nickName>` | Home side. Required. Must be the side listed at home |
| `--away <nickName>` | Away side. Required |
| `--round <n>` | Restrict to one round. Recommended — fails fast on a wrong pairing |
| `--season <yyyy>` | Defaults to the current NRL season |
| `--question "<text>"` | An extra question for the judge to address |
| `--force-refresh` | Bypass the scene and research caches and re-fetch |
| `--provider <name>` | `ollama`, `openai`, `anthropic`, `gemini`, `bedrock` — this run only |
| `--model <id>` | Override the provider's model, this run only |
| `--show-config` | Print the resolved configuration and exit |
| `-v`, `--verbose` | Debug logging, including the LLM library's own output |

### Whole round

```bash
uv run python -m agent_app.harness run   --season 2026 --round 23 [flags]
uv run python -m agent_app.harness score --season 2026 --round 23
```

| Flag | Effect |
| --- | --- |
| `--dry-run` | List fixtures, kickoffs and what a real run would do. No LLM |
| `--only <TEAM>` | Limit to fixtures involving TEAM. Repeatable |
| `--repredict` | Re-run fixtures already predicted, replacing their entries |
| `--force-refresh` | Bypass the caches |
| `--provider`, `--model`, `-v` | As above |

### Checks

```bash
uv run python scripts/smoke_orchestrator.py              # 2s, offline, whole loop
cd ../tools/mcp_gateway && uv run python scripts/smoke_tools.py   # ~2min, live tools
```

### Switching to a hosted model

Put the key in `agent/.env` (copy `agent/.env.example`), then change one line in
`config.toml`:

```toml
[llm]
provider = "openai"     # ollama | openai | anthropic | gemini | bedrock
```

Each provider has a `[llm.presets.*]` block with its model, so switching
provider brings the right model with it. A hosted provider takes a run from
8–15 minutes to well under one. Verify with `--show-config`, which redacts the
key itself.

Precedence, lowest to highest: built-in defaults, `config.toml`, `agent/.env`,
environment variables, CLI flags.

---

## 10. When something goes wrong

| Symptom | Cause and fix |
| --- | --- |
| `No module named agent_app` | You are not in `agent/`. `cd agent` |
| Exit code `2`, "missing credentials" | A hosted provider is selected without its API key. Add it to `agent/.env`, or switch `config.toml` back to `ollama` |
| `scene_failed: All retries failed for https://www.nrl.com/draw/…` | No network, or nrl.com is unreachable. Retry |
| `fixture_not_found` | Wrong pairing, wrong home/away order, or wrong round. The error lists the round's real fixtures — copy from it |
| `model_not_trained` | The model artifact is missing. Retrain: `cd tools/mathematical_engine && uv run python -m model.train` |
| Nothing happens for three to five minutes | Normal. A judgement or verifier call on `gemma4:31b-mlx` (with thinking) takes about that long. The stage banners show progress; every call is bounded by a 600-second timeout |
| Verifier times out / hangs near the end | Usually two agent runs fighting over the same local model. Wait for the first to finish, confirm `ollama ps` is idle, then retry one fixture |
| Connection refused on `127.0.0.1:11434` | `ollama serve` is not running |
| Run failed partway | The ledger is still written, with `error` naming the stage that failed and every completed tool call preserved. Open it before rerunning |
| Research kept an irrelevant article | Its `keep_reasons` in the ledger says which rule admitted it |
| Research missed something you expected | `tools/qualitative_research/debug/dropped/<key>.json` names the rule that rejected it |
| Verifier says `unable` on a check | It could not find the evidence it needed. Read the `evidence` field — that is a real finding, not a bug |
| A round summary looks too good | Check `predicted_at` against `kickoff` per fixture in `predictions.json`. Every prediction should precede its kickoff |
| A run finished but no row appeared in `predictions_log.csv` | A spreadsheet had the file locked. `record.json` in the run folder has the same numbers; add the row by hand, then close the file before the next run |
| Confidence looks higher than you would like | Expected, and deliberate: it is the agent's own number and is no longer pulled toward the model (DD-41). Compare `confidence` against `math_home_win_prob` in the log — the gap is a finding worth reporting |

### Further reading

| Document | What it covers |
| --- | --- |
| [`README.md`](README.md) | The project, the pipeline, team nickNames |
| [`Architecture.md`](Architecture.md) | System, control-loop and data-flow diagrams |
| [`Limitations.md`](Limitations.md) | Honest accuracy, the 70% question, what it cannot do |
| [`key_design_decisions.md`](key_design_decisions.md) | Every design crossroads and its reasoning (DD-01 to DD-42) |
| [`Glossary.md`](Glossary.md) | Plain-English definitions of the ML and agent terms |
| [`agent/README.md`](agent/README.md) | Agent setup, loops, verifier guardrails |
| [`agent/adrs/`](agent/adrs/) | The agent's design records, one decision each |
| [`agent_runs/README.md`](agent_runs/README.md) | Output layout and how to read a ledger |
