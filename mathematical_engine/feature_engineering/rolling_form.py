"""Pillars C, D, E: rolling short-term form, momentum, and workload features.

Approach: explode each match into two team-perspective records, sort each
team's records chronologically, shift by one game (so a match never sees
its own stats), take rolling means, then merge back as home/away columns
and reduce to home-minus-away differentials.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Pillar C telemetry: flat-table column stem -> feature stem.
TELEMETRY_STATS = {
    "post_contact_metres": "post_contact_metres",
    "kicking_metres": "kicking_metres",
    "play_the_ball_speed": "play_the_ball_speed",
    "possession_pct": "possession_pct",
    "completion_rate": "completion_rate",
    "effective_tackle_pct": "effective_tackle_pct",
    "missed_tackles": "missed_tackles",
    "errors": "errors",
    "penalties_conceded": "penalties_conceded",
    "line_breaks": "line_breaks",
    "tackle_breaks": "tackle_breaks",
    "offloads": "offloads",
    "all_run_metres": "all_run_metres",
    "forced_drop_outs": "forced_drop_outs",
    # decoy_runs proxy removed: lineEngagedRuns is zero in every match (dead field)
    "support_plays": "support_plays",    # proxy: lineBreakAssists + tryAssists
}

FORM_WINDOWS = (3, 5)
MOMENTUM_WINDOW = 5
WORKLOAD_WINDOW = 5


def build_team_perspective(df: pd.DataFrame) -> pd.DataFrame:
    """Two rows per match: each team's stats from its own perspective."""
    sides = []
    for side, opp in (("home", "away"), ("away", "home")):
        cols = {
            "match_id": df["match_id"],
            "team_id": df[f"{side}_team_id"],
            "start_time": df["start_time"],
            "side": side,
            # Pillar C + points
            "points_for": df[f"{side}_score"],
            "points_against": df[f"{opp}_score"],
            # Pillar D
            "last20_net_points": df[f"{side}_last20_points"] - df[f"{opp}_last20_points"],
            "first_to_score": (df["first_scorer"] == side).astype(float),
            "penalty_gap_seconds": df[f"{side}_penalty_gap_seconds"],
            "penalty_clusters": df[f"{side}_penalty_clusters"],
            # Pillar E
            "top3_run_metre_share": df[f"{side}_top3_run_metre_share"],
            "top3_tackle_share": df[f"{side}_top3_tackle_share"],
        }
        for col_stem in TELEMETRY_STATS:
            cols[col_stem] = df[f"{side}_{col_stem}"]
        sides.append(pd.DataFrame(cols))

    long_df = pd.concat(sides, ignore_index=True)
    return long_df.sort_values(["team_id", "start_time"]).reset_index(drop=True)


def compute_rolling(long_df: pd.DataFrame) -> pd.DataFrame:
    """Shifted rolling means per team (pre-match values only)."""
    grouped = long_df.groupby("team_id", sort=False)
    out = long_df[["match_id", "side"]].copy()

    def rolled(col: str, window: int) -> pd.Series:
        return grouped[col].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        )

    for stem, feature in TELEMETRY_STATS.items():
        for w in FORM_WINDOWS:
            out[f"form{w}_{feature}"] = rolled(stem, w)
    for w in FORM_WINDOWS:
        out[f"form{w}_points_for"] = rolled("points_for", w)
        out[f"form{w}_points_against"] = rolled("points_against", w)

    out[f"mom{MOMENTUM_WINDOW}_last20_net_points"] = rolled("last20_net_points", MOMENTUM_WINDOW)
    out[f"mom{MOMENTUM_WINDOW}_penalty_gap_seconds"] = rolled("penalty_gap_seconds", MOMENTUM_WINDOW)
    out[f"mom{MOMENTUM_WINDOW}_penalty_cluster_rate"] = rolled("penalty_clusters", MOMENTUM_WINDOW)
    out[f"mom{MOMENTUM_WINDOW}_first_to_score_rate"] = rolled("first_to_score", MOMENTUM_WINDOW)

    out[f"wl{WORKLOAD_WINDOW}_top3_run_metre_share"] = rolled("top3_run_metre_share", WORKLOAD_WINDOW)
    out[f"wl{WORKLOAD_WINDOW}_top3_tackle_share"] = rolled("top3_tackle_share", WORKLOAD_WINDOW)
    return out


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Attach rolling form/momentum/workload differentials to the match df."""
    assert df["start_time"].is_monotonic_increasing, "df must be sorted by start_time"

    long_df = build_team_perspective(df)
    rolling = compute_rolling(long_df)

    feature_cols = [c for c in rolling.columns if c not in ("match_id", "side")]
    home = rolling[rolling["side"] == "home"].set_index("match_id")[feature_cols]
    away = rolling[rolling["side"] == "away"].set_index("match_id")[feature_cols]
    diffs = (home - away).add_suffix("_diff")

    df = df.merge(diffs, left_on="match_id", right_index=True, how="left")
    logger.info("Computed %d rolling differential features", len(diffs.columns))
    return df
