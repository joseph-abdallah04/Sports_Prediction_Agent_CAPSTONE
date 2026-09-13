# Raw Data Lake: Quality Findings for Phase 2 Planning

Findings from the completed historical backfill (Job A), run 12 June 2026.
These must be accounted for when designing the Phase 2 transformations and
feature engineering described in [Overview.md](Overview.md).

## Backfill outcome

- **2,324 matches** scraped across seasons 2015–2026, **zero failures**.
- ~313 MB of raw, untransformed JSON in `data_lake/raw_historical/{season}/`.
- Core telemetry verified present in **every** season back to 2015:
  `match.stats.groups` (team stats), `match.timeline` (event stream with
  `gameSeconds`), per-player stats (59 fields incl. `postContactMetres`),
  final scores, venue.
- Re-validate at any time with: `uv run python -m historical_data_backfill_etl.validate`

## Season coverage

| Season | Matches | Notes |
| --- | --- | --- |
| 2015–2019 | 201 each | Full seasons (incl. finals) |
| 2020 | 169 | COVID-shortened season — genuinely fewer games |
| 2021–2022 | 201 each | |
| 2023–2025 | 213 each | Competition expanded (17 teams, extra round) |
| 2026 | 109 | Season in progress; weekly pipeline (Job B) will collect the rest |

## Finding 1: Weather field is unreliable

`match.weather` is missing in **832 of 2,324 matches (~36%)**, and the gaps
are not random:

| Season | Missing weather |
| --- | --- |
| 2015 | 111 / 201 |
| 2016–2019 | 13 total (near-complete) |
| 2020 | 141 / 169 |
| 2021 | 52 / 201 |
| 2022 | 91 / 201 |
| 2023 | 213 / 213 (all) |
| 2024 | 210 / 213 |
| 2025–2026 | 1 total (near-complete) |

**Implication for Phase 2:** the "Weather Modifiers" feature (Overview
Pillar B) cannot rely on this field alone. Options: treat missing as an
explicit "unknown" category, or join an external weather source by venue
city + match date. Decide during transformation planning.

## Finding 2: Stat definitions drifted across eras

The set of team stats in `stats.groups` is not constant across seasons:

- **2015** lacks "Completion Rate", team "Errors", and "Average Set
  Distance" (present in modern seasons).
- **`SetRestart` timeline events only exist from 2020** — the six-again
  rule was introduced that year. Earlier seasons express the equivalent
  pressure via `Penalty` / `RuckInfringement` events.

**Implication for Phase 2:** when flattening, missing-by-era stats are
legitimately absent, not data errors. Features built on them must either
be derivable from other fields for old seasons, restricted to the seasons
where they exist, or encoded with an era-aware default. Penalty-cluster
features (Overview Pillar D) should treat pre-2020 and post-2020
discipline signals consistently.

## Finding 3: Four phantom (cancelled) games must be excluded

Four fixtures are recorded as 0–0 "FullTime" with empty stats and a
2-event timeline — COVID-era cancelled games that nrl.com kept as pages:

| File | Fixture |
| --- | --- |
| `2020/nrl_match_20201110840.json` | Titans v Sharks |
| `2021/nrl_match_20211110780.json` | Storm v Warriors |
| `2021/nrl_match_20211111340.json` | Knights v Eels |
| `2021/nrl_match_20211111930.json` | Cowboys v Storm |

**Implication for Phase 2:** the transform step must filter these out
(simple rule: drop matches where `stats.groups` is empty). They must not
contribute rows to training data, and must not count as games played in
rolling-window calculations (Elo, Pythagorean, form averages).
