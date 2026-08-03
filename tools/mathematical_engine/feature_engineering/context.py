"""Pillar B: environmental context features (rest, venue HGA, weather, travel).

The binary ctx_travel_away flag is computed in Stage 1 (flatten.py); the
kilometre-scale travel features are computed here from venue coordinates.
All values here are strictly pre-match.
"""

import logging

import numpy as np
import pandas as pd

from .flatten import TEAM_HOME_COORDS, VENUE_TO_COORDS

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0

# A turnaround under six days is the recognised short break in the NRL draw
# (e.g. Sunday then the following Friday) and is widely treated as a real
# disadvantage. Keep it as an explicit flag: tree models can split on
# rest-days directly, but the flag makes the threshold learnable from far
# fewer examples and keeps the SHAP explanation legible.
SHORT_TURNAROUND_DAYS = 6.0

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


def add_short_turnaround(df: pd.DataFrame) -> pd.DataFrame:
    """Flag sides backing up on fewer than six days' rest."""
    df = df.copy()
    for side in ("home", "away"):
        rest = df[f"ctx_rest_days_{side}"]
        flag = (rest < SHORT_TURNAROUND_DAYS).astype(float)
        # A team's first ever match has no rest value; do not invent one.
        df[f"ctx_short_turnaround_{side}"] = flag.where(rest.notna())
    df["ctx_short_turnaround_diff"] = (
        df["ctx_short_turnaround_home"] - df["ctx_short_turnaround_away"]
    )
    return df


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = np.radians(a)
    lat2, lon2 = np.radians(b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(h)))


def _travel_km(team_id, venue: str | None) -> float:
    """Great-circle distance from a team's home base to the match venue."""
    home = TEAM_HOME_COORDS.get(team_id)
    stadium = VENUE_TO_COORDS.get(venue) if isinstance(venue, str) else None
    if home is None or stadium is None:
        return np.nan
    return _haversine_km(home, stadium)


def add_travel_distance(df: pd.DataFrame) -> pd.DataFrame:
    """Kilometres each side travelled to the venue, and the difference.

    The existing ctx_travel_away flag only says whether the away side left its
    home state. Distance separates a cross-town trip from a Townsville-to-
    Auckland haul, and covers "home" games played away from a club's own
    ground (Magic Round, Las Vegas), where the nominal home side travels too.
    """
    df = df.copy()
    venues = df["venue"].tolist()
    for side in ("home", "away"):
        team_ids = df[f"{side}_team_id"].tolist()
        df[f"ctx_travel_km_{side}"] = [
            _travel_km(t, v) for t, v in zip(team_ids, venues)
        ]
    df["ctx_travel_km_diff"] = df["ctx_travel_km_home"] - df["ctx_travel_km_away"]
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
    df = add_short_turnaround(df)
    df = add_travel_distance(df)
    df = add_venue_hga(df)
    df = add_weather_category(df)
    logger.info(
        "Computed context features (rest days, turnaround, travel, venue HGA, weather)"
    )
    return df
