"""Stage 1: flatten raw match JSONs into one row of post-match facts per match.

Reads every file in data_lake/raw_historical/ and writes
feature_store/matches_flat.parquet. Each row records what HAPPENED in that
match (scores, team telemetry, timeline aggregates, player workload).
Pre-match rolling features are computed later in Stage 2.

Guardrails (agreed in the Phase 2 plan):
1. Venue-to-state dictionary hardcoded below; unknown venues default
   ctx_travel_away to 0 and print a warning.
2. Strictly binary outcomes: draws and the 4 phantom COVID games are
   dropped before the Parquet is written.
3. NaN rule: era-missing telemetry is never imputed; left as NaN for
   XGBoost's native missing-value handling.

Usage:
    uv run python -m feature_engineering.flatten
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("flatten")

ENGINE_ROOT = Path(__file__).resolve().parents[1]
RAW_HISTORICAL_DIR = ENGINE_ROOT / "data_lake" / "raw_historical"
FEATURE_STORE_DIR = ENGINE_ROOT / "feature_store"
OUTPUT_PATH = FEATURE_STORE_DIR / "matches_flat.parquet"

# ---------------------------------------------------------------------------
# Venue-to-state dictionary (guardrail 1).
# Locations verified against the venueCity field in the raw data itself.
# Includes legacy/sponsor name variants (ANZ vs Accor, 1300SMILES, Lottoland...).
# ---------------------------------------------------------------------------
VENUE_TO_STATE = {
    # NSW (incl. Sydney metro legacy names)
    "Accor Stadium": "NSW",
    "ANZ Stadium": "NSW",
    "Stadium Australia": "NSW",
    "CommBank Stadium": "NSW",
    "Allianz Stadium": "NSW",
    "Sydney Cricket Ground": "NSW",
    "4 Pines Park": "NSW",
    "Lottoland": "NSW",
    "BlueBet Stadium": "NSW",
    "Penrith Park": "NSW",
    "PointsBet Stadium": "NSW",
    "Sharks Stadium": "NSW",
    "Southern Cross Stadium": "NSW",
    "Netstrata Jubilee Stadium": "NSW",
    "Jubilee Stadium": "NSW",
    "St George Venues Jubilee Stadium": "NSW",
    "Ocean Protect Stadium": "NSW",
    "Belmore Sports Ground": "NSW",
    "Leichhardt Oval": "NSW",
    "Campbelltown Sports Stadium": "NSW",
    "Campbelltown Stadium": "NSW",
    "McDonald Jones Stadium": "NSW",
    "WIN Stadium": "NSW",
    "Central Coast Stadium": "NSW",
    "Industree Group Stadium": "NSW",
    "Polytec Stadium": "NSW",
    "Carrington Park": "NSW",
    "Scully Park": "NSW",
    "Glen Willow Oval": "NSW",
    "Apex Oval": "NSW",
    "McDonalds Park": "NSW",
    "Geohex Park": "NSW",
    "C.ex Coffs International Stadium": "NSW",
    # QLD
    "Suncorp Stadium": "QLD",
    "The Gabba": "QLD",
    "Cbus Super Stadium": "QLD",
    "Kayo Stadium": "QLD",
    "Moreton Daily Stadium": "QLD",
    "Queensland Country Bank Stadium": "QLD",
    "1300SMILES Stadium": "QLD",
    "Sunshine Coast Stadium": "QLD",
    "Barlow Park": "QLD",
    "BB Print Stadium": "QLD",
    "Browne Park": "QLD",
    "Salter Oval": "QLD",
    "Marley Brown Oval": "QLD",
    "Clive Berghofer Stadium": "QLD",
    # VIC / ACT / SA / WA / NT
    "AAMI Park": "VIC",
    "Marvel Stadium": "VIC",
    "GIO Stadium": "ACT",
    "Adelaide Oval": "SA",
    "Optus Stadium": "WA",
    "HBF Park": "WA",
    "TIO Stadium": "NT",
    # New Zealand
    "Go Media Stadium": "NZ",
    "Mt Smart Stadium": "NZ",
    "Sky Stadium": "NZ",
    "Hnry Stadium": "NZ",
    "FMG Stadium Waikato": "NZ",
    "McLean Park": "NZ",
    "Yarrow Stadium": "NZ",
    "Forsyth Barr Stadium": "NZ",
    "Christchurch Stadium": "NZ",
    "Apollo Projects Stadium": "NZ",
    # International one-offs
    "Allegiant Stadium": "USA",
    "The Mend-A-Hose Jungle": "UK",
}

# Home state per franchise, keyed by stable NRL teamId.
TEAM_HOME_STATE = {
    500001: "NSW",  # Roosters
    500002: "NSW",  # Sea Eagles
    500003: "NSW",  # Knights
    500004: "QLD",  # Titans
    500005: "NSW",  # Rabbitohs
    500010: "NSW",  # Bulldogs
    500011: "QLD",  # Broncos
    500012: "QLD",  # Cowboys
    500013: "ACT",  # Raiders
    500014: "NSW",  # Panthers
    500021: "VIC",  # Storm
    500022: "NSW",  # Dragons
    500023: "NSW",  # Wests Tigers
    500028: "NSW",  # Sharks
    500031: "NSW",  # Eels
    500032: "NZ",   # Warriors
    500723: "QLD",  # Dolphins
}

# Team stat titles (stats.groups) -> column names. Anything not listed is
# normalised generically; "Used" needs its group for disambiguation.
STAT_TITLE_OVERRIDES = {
    "Possession %": "possession_pct",
    "Kick Defusal %": "kick_defusal_pct",
    "Effective Tackle %": "effective_tackle_pct",
    "Average Play The Ball Speed": "play_the_ball_speed",
    "40/20": "forty_twenty",
    "Inside 10 Metres": "inside_ten_metres",
}

# Timeline event type -> points scored.
SCORING_EVENT_POINTS = {
    "Try": 4,
    "Goal": 2,
    "OnePointFieldGoal": 1,
    "TwoPointFieldGoal": 2,
}

# Discipline events conceded by `teamId` (semantics verified: event counts
# match the "Penalties Conceded" team stat exactly). SetRestart and
# RuckInfringement only exist from 2020 (six-again era).
DISCIPLINE_EVENT_TYPES = {"Penalty", "SetRestart", "RuckInfringement"}

REGULATION_START_LAST20 = 3600  # gameSeconds
REGULATION_END = 4800
PENALTY_CLUSTER_WINDOW_SECONDS = 300
PENALTY_CLUSTER_MIN_EVENTS = 3


def normalise_stat_title(title: str) -> str:
    if title in STAT_TITLE_OVERRIDES:
        return STAT_TITLE_OVERRIDES[title]
    if title == "Used":  # Interchanges group
        return "interchanges_used"
    name = title.lower().replace("%", "pct")
    name = "".join(c if c.isalnum() else "_" for c in name)
    while "__" in name:
        name = name.replace("__", "_")
    return name.strip("_")


def parse_team_stats(match: dict) -> dict:
    """Flatten stats.groups into {home_<stat>: v, away_<stat>: v}."""
    row = {}
    for group in match.get("stats", {}).get("groups") or []:
        for stat in group.get("stats") or []:
            title = stat.get("title")
            if not title:
                continue
            col = normalise_stat_title(title)
            row[f"home_{col}"] = (stat.get("homeValue") or {}).get("value")
            row[f"away_{col}"] = (stat.get("awayValue") or {}).get("value")
    return row


def count_penalty_clusters(event_seconds: list[int]) -> int:
    """Count non-overlapping bursts of 3+ discipline events within 5 minutes."""
    times = sorted(event_seconds)
    clusters = 0
    i = 0
    while i < len(times):
        window_end = times[i] + PENALTY_CLUSTER_WINDOW_SECONDS
        j = i
        while j < len(times) and times[j] <= window_end:
            j += 1
        if j - i >= PENALTY_CLUSTER_MIN_EVENTS:
            clusters += 1
            i = j  # consume the burst so overlapping windows don't double count
        else:
            i += 1
    return clusters


def parse_timeline(match: dict) -> dict:
    """Aggregate the timeline into per-team momentum/discipline facts."""
    home_id = match["homeTeam"]["teamId"]
    timeline = match.get("timeline") or []

    last20_points = {"home": 0, "away": 0}
    first_scorer = None
    first_score_seconds = None
    discipline_seconds = {"home": [], "away": []}

    for event in timeline:
        etype = event.get("type")
        seconds = event.get("gameSeconds")
        team_id = event.get("teamId")
        if seconds is None or team_id is None:
            continue
        side = "home" if team_id == home_id else "away"

        if etype in SCORING_EVENT_POINTS:
            if first_score_seconds is None or seconds < first_score_seconds:
                first_score_seconds = seconds
                first_scorer = side
            if REGULATION_START_LAST20 <= seconds <= REGULATION_END:
                last20_points[side] += SCORING_EVENT_POINTS[etype]
        elif etype in DISCIPLINE_EVENT_TYPES and seconds <= REGULATION_END:
            discipline_seconds[side].append(seconds)

    row = {
        "home_last20_points": last20_points["home"],
        "away_last20_points": last20_points["away"],
        "first_scorer": first_scorer,
    }
    for side in ("home", "away"):
        times = sorted(discipline_seconds[side])
        gaps = [b - a for a, b in zip(times, times[1:])]
        row[f"{side}_penalty_gap_seconds"] = (sum(gaps) / len(gaps)) if gaps else None
        row[f"{side}_penalty_clusters"] = count_penalty_clusters(times)
    return row


def parse_player_aggregates(match: dict, side: str) -> dict:
    """Team-level aggregates derived from per-player stats.

    Includes the agreed support-plays proxy (lineBreakAssists + tryAssists;
    no direct field exists in the NRL payload) plus top-3 workload
    concentration shares. Note: a decoy-runs proxy via lineEngagedRuns was
    planned but dropped - that field is zero in all 2,311 matches (present
    in the schema, never populated by NRL).
    """
    players = match.get("stats", {}).get("players", {}).get(f"{side}Team") or []
    if not players:
        return {}

    def total(field: str) -> float:
        return sum(p.get(field) or 0 for p in players)

    row = {
        f"{side}_support_plays": total("lineBreakAssists") + total("tryAssists"),
        f"{side}_player_errors_total": total("errors"),
    }

    run_metres = sorted((p.get("allRunMetres") or 0 for p in players), reverse=True)
    tackles = sorted((p.get("tacklesMade") or 0 for p in players), reverse=True)
    if sum(run_metres) > 0:
        row[f"{side}_top3_run_metre_share"] = sum(run_metres[:3]) / sum(run_metres)
    if sum(tackles) > 0:
        row[f"{side}_top3_tackle_share"] = sum(tackles[:3]) / sum(tackles)
    return row


def flatten_match(path: Path, unknown_venues: set[str]) -> dict | None:
    """Convert one raw JSON file into a flat facts row (or None to drop)."""
    with open(path, encoding="utf-8") as f:
        match = json.load(f)["match"]

    # Guardrail 2a: phantom COVID games have no team stats at all.
    if not match.get("stats", {}).get("groups"):
        logger.info("Dropping phantom game (no stats): %s", path.name)
        return None

    home, away = match["homeTeam"], match["awayTeam"]
    home_score, away_score = home.get("score"), away.get("score")

    # Guardrail 2b: strictly binary outcomes - drop draws.
    if home_score == away_score:
        logger.info(
            "Dropping draw %s v %s (%s all): %s",
            home.get("nickName"), away.get("nickName"), home_score, path.name,
        )
        return None

    venue = match.get("venue")
    venue_state = VENUE_TO_STATE.get(venue)
    if venue_state is None:
        if venue not in unknown_venues:
            unknown_venues.add(venue)
            print(f"WARNING: unknown venue '{venue}' - ctx_travel_away defaulted to 0. "
                  f"Add it to VENUE_TO_STATE in flatten.py.")
        travel_away = 0
    else:
        away_state = TEAM_HOME_STATE.get(away["teamId"])
        travel_away = 1 if (away_state is not None and venue_state != away_state) else 0

    row = {
        "match_id": str(match["matchId"]),
        "season": int(path.parent.name),
        "round_number": match.get("roundNumber"),
        "start_time": match.get("startTime"),
        "venue": venue,
        "venue_state": venue_state,
        "weather": match.get("weather"),
        "ground_conditions": match.get("groundConditions"),
        "attendance": match.get("attendance"),
        "home_team_id": home["teamId"],
        "home_team": home.get("nickName"),
        "away_team_id": away["teamId"],
        "away_team": away.get("nickName"),
        "home_score": home_score,
        "away_score": away_score,
        "home_win": 1 if home_score > away_score else 0,
        "has_extra_time": bool(match.get("hasExtraTime")),
        "ctx_travel_away": travel_away,
    }
    row.update(parse_team_stats(match))
    row.update(parse_timeline(match))
    row.update(parse_player_aggregates(match, "home"))
    row.update(parse_player_aggregates(match, "away"))

    # NaN-rule-compliant derivation: 2015 has no team "Errors" stat, but the
    # raw payload carries exact per-player error counts - sum, don't impute.
    for side in ("home", "away"):
        if row.get(f"{side}_errors") is None:
            row[f"{side}_errors"] = row.get(f"{side}_player_errors_total")
    row.pop("home_player_errors_total", None)
    row.pop("away_player_errors_total", None)

    return row


def build_flat_table() -> pd.DataFrame:
    files = sorted(RAW_HISTORICAL_DIR.glob("*/nrl_match_*.json"))
    if not files:
        raise FileNotFoundError(f"No raw match files under {RAW_HISTORICAL_DIR}")

    unknown_venues: set[str] = set()
    rows = []
    for path in files:
        row = flatten_match(path, unknown_venues)
        if row is not None:
            rows.append(row)

    df = pd.DataFrame(rows)
    df["start_time"] = pd.to_datetime(df["start_time"], utc=True)
    df = df.sort_values("start_time").reset_index(drop=True)

    logger.info(
        "Flattened %d matches (%d raw files, %d dropped as draws/phantoms)",
        len(df), len(files), len(files) - len(df),
    )
    return df


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    df = build_flat_table()
    FEATURE_STORE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    logger.info("Wrote %d rows x %d cols to %s", len(df), df.shape[1], OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
