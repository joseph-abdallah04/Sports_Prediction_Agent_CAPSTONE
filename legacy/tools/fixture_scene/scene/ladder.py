"""Competition ladder standings for the two sides in a fixture.

The math engine already derives ladder features (position, win rate, points
differential per game), but it hands the judge only SHAP driver strings such as
"Ladder points differential per game (-1.5 points)". That is unreadable without
the table behind it, and its sign is easy to misattribute. Publishing the actual
standings in the scene gives the judge the same numbers a human reads off the
ladder before kick-off.

Values are the table as it stands *entering* the requested round, because
nrl.com renders a round's ladder from matches completed before it.
"""

from __future__ import annotations

import json
import logging

from bs4 import BeautifulSoup

from .http_client import NRL_BASE, RateLimitedHttpClient

logger = logging.getLogger(__name__)

NRL_PREMIERSHIP_COMPETITION_ID = 111


class LadderDataNotFoundError(Exception):
    pass


def ladder_url(season: int, round_number: int | None = None) -> str:
    url = f"{NRL_BASE}/ladder/?competition={NRL_PREMIERSHIP_COMPETITION_ID}&season={season}"
    if round_number is not None:
        url += f"&round={round_number}"
    return url


def fetch_ladder_positions(
    client: RateLimitedHttpClient,
    season: int,
    round_number: int | None = None,
) -> tuple[list[dict], str]:
    """Ordered ladder entries (1st to last) plus the page they came from."""
    url = ladder_url(season, round_number)
    soup = BeautifulSoup(client.get_text(url), "html.parser")
    container = soup.find("div", id="vue-ladder")
    if container is None or not container.has_attr("q-data"):
        raise LadderDataNotFoundError(f"No vue-ladder data at {url}")
    positions = json.loads(container["q-data"]).get("positions") or []
    if not positions:
        raise LadderDataNotFoundError(f"Ladder at {url} listed no teams")
    return positions, url


def _num(stats: dict, key: str) -> float | None:
    value = stats.get(key)
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _standing(entry: dict, position: int) -> dict:
    """One team's row, trimmed to what a reader needs before kick-off."""
    stats = entry.get("stats") or {}
    played = _num(stats, "played")
    differential = _num(stats, "points difference")
    per_game = (
        round(differential / played, 2)
        if differential is not None and played
        else None
    )
    return {
        "team": entry.get("teamNickname"),
        "position": position,
        "played": int(played) if played is not None else None,
        "wins": int(_num(stats, "wins") or 0),
        "drawn": int(_num(stats, "drawn") or 0),
        "lost": int(_num(stats, "lost") or 0),
        "competition_points": int(_num(stats, "points") or 0),
        "points_for": int(_num(stats, "points for") or 0),
        "points_against": int(_num(stats, "points against") or 0),
        "points_difference": int(differential) if differential is not None else None,
        "points_difference_per_game": per_game,
        "recent_form_last_4": stats.get("form"),
        "streak": stats.get("streak"),
        "home_record": stats.get("home record"),
        "away_record": stats.get("away record"),
    }


def _find(positions: list[dict], nickname: str) -> dict | None:
    target = (nickname or "").strip().lower()
    for index, entry in enumerate(positions, start=1):
        if (entry.get("teamNickname") or "").strip().lower() == target:
            return _standing(entry, index)
    return None


def _comparison(home: dict, away: dict) -> dict:
    """Home-minus-away gaps, matching the math engine's sign convention.

    Positive always favours the home side, so these line up directly with the
    `ladder_*_diff` features and let the judge sanity-check a SHAP driver.
    """
    home_pd, away_pd = (
        home["points_difference_per_game"],
        away["points_difference_per_game"],
    )
    pd_gap = round(home_pd - away_pd, 2) if None not in (home_pd, away_pd) else None
    position_gap = away["position"] - home["position"]

    if pd_gap is None:
        favours = "unknown"
    elif pd_gap > 0:
        favours = home["team"]
    elif pd_gap < 0:
        favours = away["team"]
    else:
        favours = "neither"

    return {
        "higher_on_ladder": (
            home["team"] if position_gap > 0
            else away["team"] if position_gap < 0
            else "level"
        ),
        "ladder_positions_gap": position_gap,
        "points_difference_per_game_gap": pd_gap,
        "points_difference_favours": favours,
    }


def build_standings(
    client: RateLimitedHttpClient,
    *,
    home_team: str,
    away_team: str,
    season: int,
    round_number: int | None = None,
) -> dict:
    """Ladder rows for both sides, or an `error` key if they cannot be read."""
    try:
        positions, url = fetch_ladder_positions(client, season, round_number)
    except Exception as e:
        logger.warning("Ladder fetch failed season=%s round=%s: %s", season, round_number, e)
        return {"available": False, "error": str(e), "source_url": ladder_url(season, round_number)}

    home = _find(positions, home_team)
    away = _find(positions, away_team)
    if home is None or away is None:
        missing = [
            name for name, row in ((home_team, home), (away_team, away)) if row is None
        ]
        logger.warning("Ladder has no row for %s", ", ".join(missing))
        return {
            "available": False,
            "error": f"No ladder row for {', '.join(missing)}",
            "source_url": url,
        }

    return {
        "available": True,
        "as_at_round": round_number,
        "teams_in_competition": len(positions),
        "home": home,
        "away": away,
        "comparison": _comparison(home, away),
        "source_url": url,
    }
