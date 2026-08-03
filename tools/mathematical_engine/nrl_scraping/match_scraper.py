"""Extracts the raw match data payload from an NRL Match Centre page.

NRL match centre pages embed their full state as JSON inside the
`q-data` attribute of `<div id="vue-match-centre">`. This module fetches
the page and returns that payload as a Python dict.
"""

import json
import logging

from bs4 import BeautifulSoup

from .http import NRLHttpClient

logger = logging.getLogger(__name__)


class MatchDataNotFoundError(Exception):
    """The page loaded but did not contain the expected data container."""


def extract_match_data(client: NRLHttpClient, match_url: str) -> dict:
    """Fetch a match centre page and return its embedded JSON payload.

    Raises:
        requests.RequestException: network failure after retries.
        MatchDataNotFoundError: page has no vue-match-centre data layer.
        json.JSONDecodeError: data layer exists but is not valid JSON.
    """
    html = client.get_html(match_url)
    soup = BeautifulSoup(html, "html.parser")

    container = soup.find("div", id="vue-match-centre")
    if container is None or not container.has_attr("q-data"):
        raise MatchDataNotFoundError(
            f"No vue-match-centre data container found at {match_url}"
        )

    return json.loads(container["q-data"])


def get_match_id(payload: dict) -> str:
    """Return the unique match ID from a match payload."""
    match_id = payload.get("match", {}).get("matchId")
    if not match_id:
        raise MatchDataNotFoundError("Payload is missing match.matchId")
    return str(match_id)
