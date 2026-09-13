"""Extract structured match context from nrl.com match centre q-data."""

from __future__ import annotations

import json
import logging
from typing import Any

from bs4 import BeautifulSoup

from .http_client import RateLimitedHttpClient

logger = logging.getLogger(__name__)


class MatchDataNotFoundError(Exception):
    pass


def fetch_match_payload(client: RateLimitedHttpClient, match_url: str) -> dict:
    html = client.get_text(match_url)
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", id="vue-match-centre")
    if container is None or not container.has_attr("q-data"):
        raise MatchDataNotFoundError(f"No vue-match-centre at {match_url}")
    return json.loads(container["q-data"])


def _player_entry(p: dict) -> dict[str, Any] | None:
    number = p.get("number")
    first = (p.get("firstName") or "").strip()
    last = (p.get("lastName") or "").strip()
    name = f"{first} {last}".strip()
    if not name and not number:
        return None
    return {
        "number": number,
        "name": name or None,
        "position": p.get("position"),
        "player_id": p.get("playerId"),
    }


def _team_list(team: dict | None) -> list[dict[str, Any]]:
    if not team:
        return []
    players = team.get("players")
    out: list[dict[str, Any]] = []
    if isinstance(players, list):
        for p in players:
            if not isinstance(p, dict):
                continue
            entry = _player_entry(p)
            if entry:
                out.append(entry)
    elif isinstance(players, dict):
        # Some payloads nest by group
        for group in players.values():
            if not isinstance(group, list):
                continue
            for p in group:
                if isinstance(p, dict):
                    entry = _player_entry(p)
                    if entry:
                        out.append(entry)
    # Prefer jersey order
    out.sort(key=lambda x: (x["number"] is None, x["number"] or 99))
    return out


def _officials(match: dict) -> list[dict[str, str]]:
    raw = match.get("officials") or []
    out: list[dict[str, str]] = []
    for o in raw:
        if not isinstance(o, dict):
            continue
        first = (o.get("firstName") or "").strip()
        last = (o.get("lastName") or "").strip()
        name = f"{first} {last}".strip()
        if not name:
            continue
        out.append(
            {
                "position": o.get("position") or "Official",
                "name": name,
            }
        )
    return out


def enrich_from_match_centre(
    client: RateLimitedHttpClient,
    match_centre_url: str,
) -> dict[str, Any]:
    """Return fixture enrichment fields from match centre payload."""
    payload = fetch_match_payload(client, match_centre_url)
    match = payload.get("match") or payload
    home = match.get("homeTeam") or {}
    away = match.get("awayTeam") or {}
    home_list = _team_list(home)
    away_list = _team_list(away)
    if home_list or away_list:
        lists_status = "available"
    else:
        lists_status = "unavailable"

    kickoff = match.get("startTime") or match.get("kickOffTime")
    return {
        "season": (match.get("competition") or {}).get("season")
        or match.get("season"),
        "round_number": match.get("roundNumber"),
        "round_title": match.get("roundTitle"),
        "home_team": home.get("nickName"),
        "away_team": away.get("nickName"),
        "kickoff": kickoff,
        "venue": match.get("venue"),
        "venue_city": match.get("venueCity"),
        "match_mode": match.get("matchMode"),
        "match_id": match.get("matchId"),
        "ground_conditions": match.get("groundConditions"),
        "nrl_weather_field": match.get("weather"),
        "officials": _officials(match),
        "team_lists": {
            "home": home_list,
            "away": away_list,
            "status": lists_status,
        },
        "match_centre_url": match.get("url") or match_centre_url,
    }
