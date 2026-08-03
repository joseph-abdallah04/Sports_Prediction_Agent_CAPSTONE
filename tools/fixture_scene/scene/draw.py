"""Find an upcoming fixture on nrl.com draw pages via vue-draw q-data."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .http_client import NRL_BASE, RateLimitedHttpClient

logger = logging.getLogger(__name__)

NRL_PREMIERSHIP_COMPETITION_ID = 111
AU_TZ = ZoneInfo("Australia/Sydney")


class DrawDataNotFoundError(Exception):
    pass


class FixtureNotFoundError(Exception):
    pass


def fetch_draw_payload(
    client: RateLimitedHttpClient,
    season: int,
    round_number: int | None = None,
) -> tuple[dict, str]:
    if round_number is None:
        url = (
            f"{NRL_BASE}/draw/?competition={NRL_PREMIERSHIP_COMPETITION_ID}"
            f"&season={season}"
        )
    else:
        url = (
            f"{NRL_BASE}/draw/?competition={NRL_PREMIERSHIP_COMPETITION_ID}"
            f"&round={round_number}&season={season}"
        )
    html = client.get_text(url)
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", id="vue-draw")
    if container is None or not container.has_attr("q-data"):
        raise DrawDataNotFoundError(f"No vue-draw data at {url}")
    return json.loads(container["q-data"]), url


def _nick(team: dict | None) -> str:
    return ((team or {}).get("nickName") or "").strip()


def _norm(s: str) -> str:
    return s.strip().lower()


def _teams_match(fixture: dict, home: str, away: str) -> bool:
    fh = _norm(_nick(fixture.get("homeTeam")))
    fa = _norm(_nick(fixture.get("awayTeam")))
    return fh == _norm(home) and fa == _norm(away)


def _is_upcoming(fixture: dict) -> bool:
    if fixture.get("type") != "Match":
        return False
    mode = (fixture.get("matchMode") or "").strip()
    # Pre = not started; Live = in progress (still useful scene context)
    return mode in {"Pre", "Live", ""}


def list_rounds(payload: dict) -> list[int]:
    rounds = sorted(
        int(r["value"])
        for r in payload.get("filterRounds", [])
        if r.get("value") is not None
    )
    return rounds


def selected_round(payload: dict) -> int | None:
    for key in ("selectedRoundNumber", "roundNumber", "filterRound"):
        val = payload.get(key)
        if isinstance(val, int):
            return val
        if isinstance(val, dict) and val.get("value") is not None:
            try:
                return int(val["value"])
            except (TypeError, ValueError):
                pass
    # Sometimes nested under filter
    fr = payload.get("selectedFilterRound") or payload.get("round")
    if isinstance(fr, int):
        return fr
    if isinstance(fr, dict) and fr.get("value") is not None:
        try:
            return int(fr["value"])
        except (TypeError, ValueError):
            pass
    return None


def extract_fixture_card(fixture: dict, *, season: int, round_number: int, draw_url: str) -> dict[str, Any]:
    centre = fixture.get("matchCentreUrl") or fixture.get("url") or ""
    if centre and centre.startswith("/"):
        centre = NRL_BASE + centre
    clock = fixture.get("clock") if isinstance(fixture.get("clock"), dict) else {}
    kickoff = (
        clock.get("kickOffTimeLong")
        or clock.get("kickOffTime")
        or fixture.get("startTime")
        or fixture.get("kickOffTime")
    )
    return {
        "season": season,
        "round_number": round_number,
        "round_title": fixture.get("roundTitle") or f"Round {round_number}",
        "home_team": _nick(fixture.get("homeTeam")),
        "away_team": _nick(fixture.get("awayTeam")),
        "kickoff_raw": kickoff,
        "venue": fixture.get("venue"),
        "venue_city": fixture.get("venueCity"),
        "match_centre_url": centre,
        "match_mode": fixture.get("matchMode"),
        "match_id": fixture.get("matchId") or fixture.get("gameId"),
        "draw_url": draw_url,
        "fixture_card": fixture,
    }


def list_round_fixtures(
    client: RateLimitedHttpClient,
    season: int,
    round_number: int,
) -> list[dict[str, Any]]:
    """Every Premiership fixture in one round, in draw order.

    Used by the batch results harness to evaluate a whole round at once rather
    than naming each fixture by hand.
    """
    payload, draw_url = fetch_draw_payload(client, season, round_number)
    return [
        extract_fixture_card(
            fixture, season=season, round_number=round_number, draw_url=draw_url
        )
        for fixture in payload.get("fixtures", [])
        if fixture.get("type") == "Match"
    ]


def fixture_result(fixture_card: dict[str, Any]) -> dict[str, Any] | None:
    """Final score from a fixture card, or None if the match is not complete."""
    fixture = fixture_card.get("fixture_card") or {}
    if (fixture.get("matchState") or "").strip() != "FullTime":
        return None
    home_score = (fixture.get("homeTeam") or {}).get("score")
    away_score = (fixture.get("awayTeam") or {}).get("score")
    if home_score is None or away_score is None:
        return None
    home_score, away_score = int(home_score), int(away_score)
    return {
        "home_score": home_score,
        "away_score": away_score,
        "margin": home_score - away_score,
        # Draws are rare but real; the model only predicts home/away.
        "winner": (
            "home" if home_score > away_score
            else "away" if away_score > home_score
            else "draw"
        ),
    }


def find_upcoming_fixture(
    client: RateLimitedHttpClient,
    home_team: str,
    away_team: str,
    *,
    season: int | None = None,
    round_number: int | None = None,
) -> dict[str, Any]:
    """Locate home v away on the draw; return a fixture card dict."""
    season = season or datetime.now(AU_TZ).year

    # Bootstrap: current draw (no round) or requested round — learn filterRounds
    payload, draw_url = fetch_draw_payload(client, season, round_number)
    rounds = list_rounds(payload)
    if not rounds:
        raise DrawDataNotFoundError(f"No rounds for season {season}")

    payload_round = round_number if round_number is not None else selected_round(payload)

    candidates: list[int]
    if round_number is not None:
        candidates = [round_number]
    else:
        sel = selected_round(payload)
        # Prefer selected round, then scan all (upcoming often near "current")
        if sel is not None and sel in rounds:
            later = [r for r in rounds if r >= sel]
            earlier = [r for r in rounds if r < sel]
            candidates = later + list(reversed(earlier))
        else:
            candidates = rounds

    seen_rounds: set[int] = set()
    for rnd in candidates:
        if rnd in seen_rounds:
            continue
        seen_rounds.add(rnd)
        if payload_round is not None and rnd == payload_round:
            page = payload
            page_url = draw_url
        else:
            try:
                page, page_url = fetch_draw_payload(client, season, rnd)
            except Exception as e:
                logger.warning("Draw fetch failed season=%s round=%s: %s", season, rnd, e)
                continue
        for fixture in page.get("fixtures", []):
            if not _is_upcoming(fixture):
                continue
            if _teams_match(fixture, home_team, away_team):
                return extract_fixture_card(
                    fixture, season=season, round_number=rnd, draw_url=page_url
                )

    # Fallback: also accept Post if that is all that exists (already played)
    for rnd in candidates:
        try:
            page, page_url = fetch_draw_payload(client, season, rnd)
        except Exception:
            continue
        for fixture in page.get("fixtures", []):
            if fixture.get("type") != "Match":
                continue
            if _teams_match(fixture, home_team, away_team):
                card = extract_fixture_card(
                    fixture, season=season, round_number=rnd, draw_url=page_url
                )
                card["note"] = "Fixture found but matchMode is not Pre/Live"
                return card

    message = (
        f"No fixture found for {home_team} v {away_team} in season {season}"
        + (f" round {round_number}" if round_number is not None else "")
    )
    # Usually a wrong round or a home/away swap, both of which the draw answers.
    if round_number is not None:
        try:
            listing = ", ".join(
                f"{c['home_team']} v {c['away_team']}"
                for c in list_round_fixtures(client, season, round_number)
            )
        except Exception:
            listing = ""
        if listing:
            message += f". Round {round_number} is: {listing}"
    raise FixtureNotFoundError(message)
