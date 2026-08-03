"""Pillar F: competition standing and head-to-head matchup history.

Every value is strictly PRE-match: the numbers attached to a row reflect the
competition table and meeting history *before* that match kicked off, built
only from earlier matches. Input must be sorted chronologically by start_time.

These features encode what a human reads off the ladder before a game — who is
higher, who is scoring more than they concede, and how this specific pairing
has recently gone — none of which Elo/Bradley-Terry express directly.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Meetings between the same two clubs considered for head-to-head features.
H2H_WINDOW = 5


def _is_number(value) -> bool:
    """True for a real numeric score (guards the synthetic inference row)."""
    if value is None or value is pd.NA:
        return False
    try:
        return not np.isnan(float(value))
    except (TypeError, ValueError):
        return False


def _ladder_rank(
    standings: dict[int, dict[str, float]],
    team_id: int,
) -> float:
    """1-based ladder position, NRL ordering: wins first, then for-and-against.

    Teams yet to play this season are unranked (NaN).
    """
    played = {t: s for t, s in standings.items() if s["games"] > 0}
    if team_id not in played:
        return np.nan
    ordered = sorted(
        played.items(),
        key=lambda kv: (kv[1]["wins"], kv[1]["points_for"] - kv[1]["points_against"]),
        reverse=True,
    )
    for position, (t, _) in enumerate(ordered, start=1):
        if t == team_id:
            return float(position)
    return np.nan


def add_ladder_features(df: pd.DataFrame) -> pd.DataFrame:
    """Season-to-date ladder position, win rate, and points differential."""
    n = len(df)
    win_pct = {"home": np.full(n, np.nan), "away": np.full(n, np.nan)}
    pts_pgm = {"home": np.full(n, np.nan), "away": np.full(n, np.nan)}
    position = {"home": np.full(n, np.nan), "away": np.full(n, np.nan)}

    season_standings: dict[int, dict[int, dict[str, float]]] = {}

    for i, row in enumerate(df.itertuples(index=False)):
        standings = season_standings.setdefault(row.season, {})
        for team_id in (row.home_team_id, row.away_team_id):
            standings.setdefault(
                team_id,
                {"games": 0.0, "wins": 0.0, "points_for": 0.0, "points_against": 0.0},
            )

        for side, team_id in (
            ("home", row.home_team_id),
            ("away", row.away_team_id),
        ):
            record = standings[team_id]
            if record["games"] > 0:
                win_pct[side][i] = record["wins"] / record["games"]
                pts_pgm[side][i] = (
                    record["points_for"] - record["points_against"]
                ) / record["games"]
            position[side][i] = _ladder_rank(standings, team_id)

        if not (_is_number(row.home_score) and _is_number(row.away_score)):
            continue  # unplayed fixture (inference row) contributes nothing

        home_score = float(row.home_score)
        away_score = float(row.away_score)
        for team_id, scored, conceded, won in (
            (row.home_team_id, home_score, away_score, row.home_win),
            (row.away_team_id, away_score, home_score, 1 - row.home_win),
        ):
            record = standings[team_id]
            record["games"] += 1
            record["wins"] += float(won)
            record["points_for"] += scored
            record["points_against"] += conceded

    out = pd.DataFrame(index=df.index)
    out["ladder_win_pct_diff"] = win_pct["home"] - win_pct["away"]
    out["ladder_pts_per_game_diff"] = pts_pgm["home"] - pts_pgm["away"]
    # Lower position is better, so away - home keeps "positive favours home".
    out["ladder_pos_diff"] = position["away"] - position["home"]
    return out


def add_head_to_head_features(df: pd.DataFrame) -> pd.DataFrame:
    """Recent meetings between the same two clubs, from the home side's view."""
    n = len(df)
    win_rate = np.full(n, np.nan)
    margin_avg = np.full(n, np.nan)
    games = np.zeros(n)

    # (min_team_id, max_team_id) -> list of (winner_team_id, margin_for_min_id)
    history: dict[tuple[int, int], list[tuple[int, float]]] = {}

    for i, row in enumerate(df.itertuples(index=False)):
        pair = (
            min(row.home_team_id, row.away_team_id),
            max(row.home_team_id, row.away_team_id),
        )
        meetings = history.get(pair, [])
        if meetings:
            window = meetings[-H2H_WINDOW:]
            games[i] = len(window)
            wins = sum(1 for winner, _ in window if winner == row.home_team_id)
            win_rate[i] = wins / len(window)
            # Stored margins are relative to pair[0]; flip when home is pair[1].
            sign = 1.0 if row.home_team_id == pair[0] else -1.0
            margin_avg[i] = sign * float(np.mean([m for _, m in window]))

        if not (_is_number(row.home_score) and _is_number(row.away_score)):
            continue

        home_score = float(row.home_score)
        away_score = float(row.away_score)
        winner = row.home_team_id if row.home_win == 1 else row.away_team_id
        margin_for_first = (
            home_score - away_score
            if row.home_team_id == pair[0]
            else away_score - home_score
        )
        history.setdefault(pair, []).append((winner, margin_for_first))

    out = pd.DataFrame(index=df.index)
    out["h2h5_win_rate"] = win_rate
    out["h2h5_margin_avg"] = margin_avg
    out["h2h5_games"] = games
    return out


def add_standings_features(df: pd.DataFrame) -> pd.DataFrame:
    """Attach all Pillar F columns to a chronologically sorted dataframe."""
    assert df["start_time"].is_monotonic_increasing, "df must be sorted by start_time"
    ladder = add_ladder_features(df)
    h2h = add_head_to_head_features(df)
    logger.info("Computed ladder standings and head-to-head(%d) features", H2H_WINDOW)
    return pd.concat([df, ladder, h2h], axis=1)
