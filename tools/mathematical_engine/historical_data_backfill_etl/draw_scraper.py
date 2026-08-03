"""Discovers match centre URLs from nrl.com draw pages.

Each draw page (e.g. /draw/?competition=111&round=5&season=2019) embeds
its state as JSON in the `q-data` attribute of `<div id="vue-draw">`.
That payload contains:
  - fixtures[]: the round's matches, each with a matchCentreUrl
  - filterRounds[]: every round that exists in the selected season
    (including finals weeks), which lets us enumerate a season exactly.
"""

import json
import logging

from bs4 import BeautifulSoup

from nrl_scraping.http import NRLHttpClient

logger = logging.getLogger(__name__)

NRL_PREMIERSHIP_COMPETITION_ID = 111


class DrawDataNotFoundError(Exception):
    """The draw page loaded but did not contain the expected data container."""


def fetch_draw_payload(client: NRLHttpClient, season: int, round_number: int) -> dict:
    """Fetch one draw page and return its embedded JSON payload."""
    url = (
        f"/draw/?competition={NRL_PREMIERSHIP_COMPETITION_ID}"
        f"&round={round_number}&season={season}"
    )
    html = client.get_html(url)
    soup = BeautifulSoup(html, "html.parser")

    container = soup.find("div", id="vue-draw")
    if container is None or not container.has_attr("q-data"):
        raise DrawDataNotFoundError(f"No vue-draw data container found at {url}")

    return json.loads(container["q-data"])


def list_season_rounds(client: NRLHttpClient, season: int) -> list[int]:
    """Return every round number that exists for a season (incl. finals)."""
    payload = fetch_draw_payload(client, season, round_number=1)
    rounds = sorted(r["value"] for r in payload.get("filterRounds", []))
    if not rounds:
        raise DrawDataNotFoundError(f"Season {season} returned no rounds")
    return rounds


def extract_completed_fixtures(payload: dict) -> list[dict]:
    """Pull completed matches out of a draw payload.

    Skips byes and matches that have not been played yet. Returns a list
    of dicts with the fields we need for the backfill manifest.
    """
    fixtures = []
    for fixture in payload.get("fixtures", []):
        if fixture.get("type") != "Match":
            continue  # byes etc.
        if fixture.get("matchMode") != "Post":
            continue  # upcoming or in-progress match
        url = fixture.get("matchCentreUrl")
        if not url:
            logger.warning("Completed fixture missing matchCentreUrl: %s", fixture)
            continue
        fixtures.append(
            {
                "match_centre_url": url,
                "round_title": fixture.get("roundTitle"),
                "home_team": fixture.get("homeTeam", {}).get("nickName"),
                "away_team": fixture.get("awayTeam", {}).get("nickName"),
            }
        )
    return fixtures


def discover_season(client: NRLHttpClient, season: int) -> list[dict]:
    """Discover all completed match URLs for one season."""
    rounds = list_season_rounds(client, season)
    logger.info("Season %d has %d rounds (%d..%d)", season, len(rounds), rounds[0], rounds[-1])

    discovered: list[dict] = []
    for round_number in rounds:
        payload = fetch_draw_payload(client, season, round_number)
        fixtures = extract_completed_fixtures(payload)
        for fixture in fixtures:
            fixture["season"] = season
            fixture["round_number"] = round_number
        discovered.extend(fixtures)
        logger.info(
            "Season %d round %d: %d completed matches", season, round_number, len(fixtures)
        )
    return discovered
