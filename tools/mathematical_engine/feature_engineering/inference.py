"""Upcoming-fixture feature builder.

The Phase 2 pipeline only computes features for matches that have already
been played (they live in the data lake as JSON). To predict a FUTURE
fixture - one with no result, no stats, no JSON - we still need the same
49 pre-match features the model trained on.

This module builds that feature vector by appending a single synthetic,
unplayed row (scores and telemetry left as NaN) to the historical flat
table and running the EXACT SAME Stage 2 code paths used for training
(ratings.py, context.py, rolling_form.py). Because every rolling/cumulative
feature depends only on earlier matches, the synthetic row - placed last in
time - picks up each team's current Elo, recent form, rest days, etc.,
with zero risk of a second feature implementation drifting from training.

Usage (programmatic):
    from feature_engineering.inference import build_fixture_features
    row = build_fixture_features("Broncos", "Storm", "Suncorp Stadium",
                                 "2026-06-20T09:30:00Z")
"""

import logging

import pandas as pd

from .build_dataset import ID_COLUMNS, LABEL_COLUMN
from .context import add_context_features
from .flatten import FEATURE_STORE_DIR, OUTPUT_PATH as FLAT_PATH, VENUE_TO_STATE, TEAM_HOME_STATE
from .ratings import add_rating_features
from .rolling_form import add_rolling_features

logger = logging.getLogger("inference")

DATASET_PATH = FEATURE_STORE_DIR / "training_dataset.parquet"
SYNTHETIC_MATCH_ID = "UPCOMING"


class FixtureError(Exception):
    """Raised when a fixture cannot be resolved (unknown team, etc.)."""


def _load_flat_table() -> pd.DataFrame:
    if not FLAT_PATH.exists():
        raise FixtureError(
            f"{FLAT_PATH} not found. Run feature_engineering.build_dataset first."
        )
    flat = pd.read_parquet(FLAT_PATH)
    flat["start_time"] = pd.to_datetime(flat["start_time"], utc=True)
    return flat


def _build_team_index(flat: pd.DataFrame) -> dict[str, int]:
    """Map team nickName (lowercased) -> stable teamId from history."""
    index: dict[str, int] = {}
    for col_name, col_id in (("home_team", "home_team_id"), ("away_team", "away_team_id")):
        for name, team_id in zip(flat[col_name], flat[col_id]):
            if isinstance(name, str):
                index[name.lower()] = int(team_id)
    return index


def feature_columns() -> list[str]:
    """The exact ordered feature list the model trains on."""
    cols = pd.read_parquet(DATASET_PATH).columns
    return [c for c in cols if c not in ID_COLUMNS + [LABEL_COLUMN]]


def _resolve_team(name: str, team_index: dict[str, int]) -> int:
    team_id = team_index.get(name.lower())
    if team_id is None:
        raise FixtureError(
            f"Unknown team '{name}'. Known teams: "
            f"{sorted({n.title() for n in team_index})}"
        )
    return team_id


def build_fixture_features(
    home_team: str,
    away_team: str,
    venue: str,
    kickoff: str | pd.Timestamp,
    weather: str | None = None,
    flat: pd.DataFrame | None = None,
) -> pd.Series:
    """Return the pre-match feature vector for a single upcoming fixture.

    Only matches that finished strictly before `kickoff` contribute, so the
    same function reproduces the historical feature vector of any past match
    (used by the parity test) and builds genuine future predictions.
    """
    if flat is None:
        flat = _load_flat_table()
    kickoff_ts = pd.to_datetime(kickoff, utc=True)

    team_index = _build_team_index(flat)
    home_id = _resolve_team(home_team, team_index)
    away_id = _resolve_team(away_team, team_index)

    # Pre-match only: discard anything at/after kickoff (essential for the
    # parity test on historical fixtures; a no-op for genuine future games).
    history = flat[flat["start_time"] < kickoff_ts].copy()

    venue_state = VENUE_TO_STATE.get(venue)
    if venue_state is None:
        logger.warning("Unknown venue '%s' - ctx_travel_away defaulted to 0.", venue)
        travel_away = 0
    else:
        away_state = TEAM_HOME_STATE.get(away_id)
        travel_away = 1 if (away_state is not None and venue_state != away_state) else 0

    # Synthetic unplayed row: identifiers/context known, results/telemetry NaN.
    synthetic = {col: pd.NA for col in flat.columns}
    synthetic.update(
        {
            "match_id": SYNTHETIC_MATCH_ID,
            "season": kickoff_ts.year,
            "round_number": pd.NA,
            "start_time": kickoff_ts,
            "venue": venue,
            "venue_state": venue_state,
            "weather": weather,
            "home_team_id": home_id,
            "home_team": home_team.title(),
            "away_team_id": away_id,
            "away_team": away_team.title(),
            "home_win": 0,  # placeholder; never read for the last row's own features
            "ctx_travel_away": travel_away,
        }
    )

    combined = pd.concat([history, pd.DataFrame([synthetic])], ignore_index=True)
    combined["start_time"] = pd.to_datetime(combined["start_time"], utc=True)
    combined = combined.sort_values("start_time").reset_index(drop=True)

    combined = add_rating_features(combined)
    combined = add_context_features(combined)
    combined = add_rolling_features(combined)

    fixture_row = combined[combined["match_id"] == SYNTHETIC_MATCH_ID].iloc[0]
    return fixture_row[feature_columns()]


def run_parity_test(n_samples: int = 5) -> bool:
    """Rebuild features for known historical matches via the inference path
    and assert they match the stored training dataset exactly.

    This guards against train/inference skew - the classic production-ML bug
    where a model is fed features computed differently than during training.
    """
    flat = _load_flat_table()
    dataset = pd.read_parquet(DATASET_PATH)
    cols = feature_columns()

    # Sample matches late enough to have full rolling history.
    candidates = dataset[dataset["season"] >= 2022].sample(
        n=n_samples, random_state=7
    )

    all_ok = True
    for _, expected in candidates.iterrows():
        meta = flat[flat["match_id"] == expected["match_id"]].iloc[0]
        rebuilt = build_fixture_features(
            home_team=meta["home_team"],
            away_team=meta["away_team"],
            venue=meta["venue"],
            kickoff=meta["start_time"],
            weather=meta["weather"],
            flat=flat,
        )
        exp_vec = pd.to_numeric(expected[cols], errors="coerce")
        got_vec = pd.to_numeric(rebuilt[cols], errors="coerce")
        # Equal where both NaN, else close.
        mismatch = ~(
            (exp_vec.isna() & got_vec.isna())
            | ((exp_vec - got_vec).abs() <= 1e-6)
        )
        label = f"{meta['home_team']} v {meta['away_team']} ({meta['match_id']})"
        if mismatch.any():
            all_ok = False
            print(f"  MISMATCH {label}: {list(exp_vec.index[mismatch])}")
        else:
            print(f"  OK       {label}")
    return all_ok


if __name__ == "__main__":
    print("Running inference parity test (historical features rebuilt via inference path)...")
    ok = run_parity_test()
    print("\nPARITY TEST PASSED" if ok else "\nPARITY TEST FAILED")
    raise SystemExit(0 if ok else 1)
