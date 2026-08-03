"""Assemble fixture scene response for the Orchestrator."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import TOOL_NAME, TOOL_VERSION
from .cache import cache_key, load as cache_load, save as cache_save
from .draw import FixtureNotFoundError, find_upcoming_fixture
from .http_client import RateLimitedHttpClient
from .match_centre import MatchDataNotFoundError, enrich_from_match_centre
from .weather import fetch_kickoff_weather

logger = logging.getLogger(__name__)
AU_TZ = ZoneInfo("Australia/Sydney")


def _to_iso_kickoff(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        text = str(raw).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=AU_TZ)
        return dt.astimezone(AU_TZ).isoformat()
    except ValueError:
        return str(raw)


def research_scene(
    home_team: str,
    away_team: str,
    *,
    season: int | None = None,
    round_number: int | None = None,
    force_refresh: bool = False,
) -> dict:
    """Resolve fixture on nrl.com + Open-Meteo weather; return SceneResponse."""
    request = {
        "home_team": home_team,
        "away_team": away_team,
        "season": season,
        "round_number": round_number,
    }
    key = cache_key(home_team, away_team, season, round_number)

    if not force_refresh:
        cached = cache_load(key)
        if cached is not None:
            cached = dict(cached)
            cached["cache_hit"] = True
            cached["retrieved_at"] = datetime.now(timezone.utc).isoformat()
            return cached

    client = RateLimitedHttpClient(delay_seconds=1.0)
    now = datetime.now(timezone.utc)

    card = find_upcoming_fixture(
        client,
        home_team,
        away_team,
        season=season,
        round_number=round_number,
    )

    match_url = card.get("match_centre_url") or ""
    enrichment: dict = {}
    match_error = None
    if match_url:
        try:
            enrichment = enrich_from_match_centre(client, match_url)
        except MatchDataNotFoundError as e:
            match_error = str(e)
            logger.warning("Match centre enrich failed: %s", e)
        except Exception as e:
            match_error = str(e)
            logger.warning("Match centre enrich failed: %s", e)

    kickoff = _to_iso_kickoff(
        enrichment.get("kickoff") or card.get("kickoff_raw")
    )
    venue = enrichment.get("venue") or card.get("venue")
    venue_city = enrichment.get("venue_city") or card.get("venue_city")

    team_lists = enrichment.get("team_lists") or {
        "home": [],
        "away": [],
        "status": "unavailable",
    }
    officials = enrichment.get("officials") or []

    fixture = {
        "season": enrichment.get("season") or card.get("season"),
        "round_number": enrichment.get("round_number") or card.get("round_number"),
        "round_title": enrichment.get("round_title") or card.get("round_title"),
        "home_team": enrichment.get("home_team") or card.get("home_team") or home_team,
        "away_team": enrichment.get("away_team") or card.get("away_team") or away_team,
        "kickoff": kickoff,
        "venue": venue,
        "venue_city": venue_city,
        "match_centre_url": enrichment.get("match_centre_url") or match_url,
        "match_mode": enrichment.get("match_mode") or card.get("match_mode"),
        "match_id": enrichment.get("match_id") or card.get("match_id"),
        "ground_conditions": enrichment.get("ground_conditions"),
        "nrl_weather_field": enrichment.get("nrl_weather_field"),
        "officials": officials,
        "team_lists": team_lists,
    }
    if card.get("note"):
        fixture["note"] = card["note"]
    if match_error:
        fixture["match_centre_error"] = match_error

    if kickoff:
        weather = fetch_kickoff_weather(
            client,
            venue=venue,
            venue_city=venue_city,
            kickoff=kickoff,
        )
    else:
        weather = {
            "provider": "open-meteo",
            "at_kickoff": None,
            "math_weather_label": "unknown",
            "source_url": None,
            "error": "No kickoff time available for forecast",
        }

    response = {
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "request": request,
        "retrieved_at": now.isoformat(),
        "cache_hit": False,
        "fixture": fixture,
        "weather": weather,
        "sources": {
            "draw_url": card.get("draw_url"),
            "match_centre_url": fixture.get("match_centre_url"),
            "weather_url": weather.get("source_url"),
        },
    }
    cache_save(key, response)
    return response
