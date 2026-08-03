"""Pillar A: long-term power ratings (Elo, Pythagorean, Bradley-Terry).

All ratings are strictly PRE-match: the value attached to a row is the
rating before that match was played, computed only from earlier matches.
Input dataframe must be sorted chronologically by start_time.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ELO_BASE = 1500.0
ELO_K = 32.0
ELO_OFFSEASON_REGRESSION = 0.30  # regress 30% toward league mean each new season

PYTHAG_WINDOW = 10
PYTHAG_EXPONENT = 2.5

BT_HALF_LIFE_DAYS = 365.0
BT_MAX_ITERATIONS = 100
BT_TOLERANCE = 1e-6


def compute_elo(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-match Elo per side with off-season mean reversion."""
    ratings: dict[int, float] = {}
    last_season: dict[int, int] = {}
    elo_home = np.empty(len(df))
    elo_away = np.empty(len(df))

    for i, row in enumerate(df.itertuples(index=False)):
        for team_id in (row.home_team_id, row.away_team_id):
            if team_id not in ratings:
                ratings[team_id] = ELO_BASE
            elif last_season.get(team_id) != row.season:
                ratings[team_id] = (
                    ELO_BASE * ELO_OFFSEASON_REGRESSION
                    + ratings[team_id] * (1 - ELO_OFFSEASON_REGRESSION)
                )
            last_season[team_id] = row.season

        h, a = ratings[row.home_team_id], ratings[row.away_team_id]
        elo_home[i], elo_away[i] = h, a

        expected_home = 1.0 / (1.0 + 10.0 ** ((a - h) / 400.0))
        delta = ELO_K * (row.home_win - expected_home)
        ratings[row.home_team_id] = h + delta
        ratings[row.away_team_id] = a - delta

    out = pd.DataFrame({"elo_home": elo_home, "elo_away": elo_away}, index=df.index)
    out["elo_diff"] = out["elo_home"] - out["elo_away"]
    return out


def compute_pythagorean(df: pd.DataFrame) -> pd.DataFrame:
    """Pythagorean expected win % over each team's previous N games."""
    history: dict[int, list[tuple[float, float]]] = {}
    pythag = {"home": np.full(len(df), np.nan), "away": np.full(len(df), np.nan)}

    for i, row in enumerate(df.itertuples(index=False)):
        for side, team_id, pf, pa in (
            ("home", row.home_team_id, row.home_score, row.away_score),
            ("away", row.away_team_id, row.away_score, row.home_score),
        ):
            games = history.setdefault(team_id, [])
            if games:
                window = games[-PYTHAG_WINDOW:]
                total_pf = sum(g[0] for g in window) ** PYTHAG_EXPONENT
                total_pa = sum(g[1] for g in window) ** PYTHAG_EXPONENT
                if total_pf + total_pa > 0:
                    pythag[side][i] = total_pf / (total_pf + total_pa)
            games.append((pf, pa))

    out = pd.DataFrame(
        {"pythag10_home": pythag["home"], "pythag10_away": pythag["away"]},
        index=df.index,
    )
    out["pythag10_diff"] = out["pythag10_home"] - out["pythag10_away"]
    return out


def _fit_bradley_terry(
    home_idx: np.ndarray,
    away_idx: np.ndarray,
    home_won: np.ndarray,
    weights: np.ndarray,
    n_teams: int,
) -> np.ndarray:
    """Weighted Bradley-Terry strengths via the MM algorithm."""
    strengths = np.ones(n_teams)
    winner_idx = np.where(home_won == 1, home_idx, away_idx)

    # Weighted win totals per team
    wins = np.zeros(n_teams)
    np.add.at(wins, winner_idx, weights)

    for _ in range(BT_MAX_ITERATIONS):
        pair_sum = strengths[home_idx] + strengths[away_idx]
        contrib = weights / pair_sum
        denom = np.zeros(n_teams)
        np.add.at(denom, home_idx, contrib)
        np.add.at(denom, away_idx, contrib)

        with np.errstate(divide="ignore", invalid="ignore"):
            updated = np.where(denom > 0, wins / denom, strengths)
        updated = np.where(updated <= 0, 1e-9, updated)
        updated /= np.exp(np.mean(np.log(updated)))  # normalise geometric mean to 1

        if np.max(np.abs(updated - strengths)) < BT_TOLERANCE:
            strengths = updated
            break
        strengths = updated
    return strengths


def compute_bradley_terry(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-match Bradley-Terry log-strength, refit before each kickoff time.

    Strictly pre-match: every match at kickoff time T is rated using only
    matches that finished before T (all matches sharing a kickoff time get
    the same fit). Refitting at kickoff granularity - rather than per round -
    keeps this feature consistent with Elo/form and lets the upcoming-fixture
    inference path reproduce it exactly. Matches are recency-weighted:
    weight = 0.5 ** (age_days / half_life).
    """
    team_ids = sorted(set(df["home_team_id"]) | set(df["away_team_id"]))
    team_index = {t: i for i, t in enumerate(team_ids)}
    n_teams = len(team_ids)

    home_idx = df["home_team_id"].map(team_index).to_numpy()
    away_idx = df["away_team_id"].map(team_index).to_numpy()
    home_won = df["home_win"].to_numpy()
    times = df["start_time"].to_numpy()

    bt_home = np.full(len(df), np.nan)
    bt_away = np.full(len(df), np.nan)

    # One fit per distinct kickoff time, using all strictly-earlier matches.
    block_starts = np.flatnonzero(np.r_[True, times[1:] != times[:-1]])

    for b, start in enumerate(block_starts):
        end = block_starts[b + 1] if b + 1 < len(block_starts) else len(df)
        if start == 0:
            continue  # no history before the earliest kickoff
        age_days = (times[start] - times[:start]) / np.timedelta64(1, "D")
        weights = 0.5 ** (age_days / BT_HALF_LIFE_DAYS)
        strengths = _fit_bradley_terry(
            home_idx[:start], away_idx[:start], home_won[:start], weights, n_teams
        )
        log_s = np.log(strengths)
        bt_home[start:end] = log_s[home_idx[start:end]]
        bt_away[start:end] = log_s[away_idx[start:end]]

    out = pd.DataFrame({"bt_home": bt_home, "bt_away": bt_away}, index=df.index)
    out["bt_diff"] = out["bt_home"] - out["bt_away"]
    return out


def add_rating_features(df: pd.DataFrame) -> pd.DataFrame:
    """Attach all Pillar A rating columns to a chronologically sorted df."""
    assert df["start_time"].is_monotonic_increasing, "df must be sorted by start_time"
    elo = compute_elo(df)
    pythag = compute_pythagorean(df)
    bt = compute_bradley_terry(df)
    logger.info("Computed Elo, Pythagorean(%d), Bradley-Terry ratings", PYTHAG_WINDOW)
    return pd.concat([df, elo, pythag, bt], axis=1)
