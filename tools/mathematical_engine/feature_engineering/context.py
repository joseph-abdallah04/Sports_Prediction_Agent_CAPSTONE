"""Pillar B: environmental context features (rest, venue HGA, weather).

ctx_travel_away is already computed in Stage 1 (flatten.py).
All values here are strictly pre-match.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Beta-smoothing for venue home-ground advantage. The prior mean is a fixed
# constant (long-run rugby league home-win rate), NOT computed from this
# dataset, so it cannot leak future information.
VENUE_HGA_PRIOR_MEAN = 0.55
VENUE_HGA_PRIOR_STRENGTH = 10.0

WEATHER_CATEGORIES = {
    "Fine": "fine",
    "Partly Cloudy": "cloudy",
    "Cloudy": "cloudy",
    "Rain": "rain",
    "Light Rain": "rain",
    "Showers": "rain",
    "Rain and Thunder": "rain",
    "Indoor": "indoor",
}


def add_rest_days(df: pd.DataFrame) -> pd.DataFrame:
    """Days since each team's previous match (NaN for a team's first game)."""
    rest = {"home": np.full(len(df), np.nan), "away": np.full(len(df), np.nan)}
    last_played: dict[int, pd.Timestamp] = {}

    for i, row in enumerate(df.itertuples(index=False)):
        for side, team_id in (("home", row.home_team_id), ("away", row.away_team_id)):
            previous = last_played.get(team_id)
            if previous is not None:
                rest[side][i] = (row.start_time - previous).total_seconds() / 86400.0
            last_played[team_id] = row.start_time

    df = df.copy()
    df["ctx_rest_days_home"] = rest["home"]
    df["ctx_rest_days_away"] = rest["away"]
    df["ctx_rest_days_diff"] = df["ctx_rest_days_home"] - df["ctx_rest_days_away"]
    return df


def add_venue_hga(df: pd.DataFrame) -> pd.DataFrame:
    """Smoothed historical home-win rate at the venue, prior matches only."""
    hga = np.empty(len(df))
    venue_games: dict[str, int] = {}
    venue_home_wins: dict[str, int] = {}

    for i, row in enumerate(df.itertuples(index=False)):
        games = venue_games.get(row.venue, 0)
        wins = venue_home_wins.get(row.venue, 0)
        hga[i] = (wins + VENUE_HGA_PRIOR_MEAN * VENUE_HGA_PRIOR_STRENGTH) / (
            games + VENUE_HGA_PRIOR_STRENGTH
        )
        venue_games[row.venue] = games + 1
        venue_home_wins[row.venue] = wins + row.home_win

    df = df.copy()
    df["ctx_venue_hga"] = hga
    return df


def add_weather_category(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise raw weather strings into a small categorical feature."""
    df = df.copy()
    df["ctx_weather"] = (
        df["weather"].map(WEATHER_CATEGORIES).fillna("unknown").astype("category")
    )
    return df


def add_context_features(df: pd.DataFrame) -> pd.DataFrame:
    assert df["start_time"].is_monotonic_increasing, "df must be sorted by start_time"
    df = add_rest_days(df)
    df = add_venue_hga(df)
    df = add_weather_category(df)
    logger.info("Computed context features (rest days, venue HGA, weather)")
    return df
