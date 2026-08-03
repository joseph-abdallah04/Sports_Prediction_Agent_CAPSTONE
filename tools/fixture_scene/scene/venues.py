"""Venue name → coordinates for Open-Meteo forecasts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlencode

if TYPE_CHECKING:
    from .http_client import RateLimitedHttpClient

logger = logging.getLogger(__name__)

# Approximate stadium coordinates (WGS84). Seeded for venues used in NRL Premiership.
VENUE_TO_COORDS: dict[str, tuple[float, float]] = {
    # NSW
    "Accor Stadium": (-33.8474, 151.0632),
    "ANZ Stadium": (-33.8474, 151.0632),
    "Stadium Australia": (-33.8474, 151.0632),
    "CommBank Stadium": (-33.8081, 150.9996),
    "Allianz Stadium": (-33.8890, 151.2254),
    "Sydney Cricket Ground": (-33.8915, 151.2247),
    "4 Pines Park": (-33.7880, 151.2860),
    "Lottoland": (-33.7880, 151.2860),
    "BlueBet Stadium": (-33.7590, 150.7090),
    "Penrith Park": (-33.7590, 150.7090),
    "PointsBet Stadium": (-34.0420, 151.1420),
    "Sharks Stadium": (-34.0420, 151.1420),
    "Southern Cross Stadium": (-34.0420, 151.1420),
    "Netstrata Jubilee Stadium": (-33.9720, 151.1290),
    "Jubilee Stadium": (-33.9720, 151.1290),
    "St George Venues Jubilee Stadium": (-33.9720, 151.1290),
    "Ocean Protect Stadium": (-33.9720, 151.1290),
    "Belmore Sports Ground": (-33.9180, 151.0880),
    "Leichhardt Oval": (-33.8740, 151.1540),
    "Campbelltown Sports Stadium": (-34.0640, 150.8040),
    "Campbelltown Stadium": (-34.0640, 150.8040),
    "McDonald Jones Stadium": (-32.9180, 151.7280),
    "WIN Stadium": (-34.4270, 150.8950),
    "Central Coast Stadium": (-33.4280, 151.3420),
    "Industree Group Stadium": (-33.4280, 151.3420),
    "Polytec Stadium": (-33.4280, 151.3420),
    "Carrington Park": (-33.4190, 149.5800),
    "Scully Park": (-31.0900, 150.9300),
    "Glen Willow Oval": (-32.3850, 149.5800),
    "Apex Oval": (-32.2450, 148.6000),
    "McDonalds Park": (-35.1250, 147.3700),
    "Geohex Park": (-35.1250, 147.3700),
    "C.ex Coffs International Stadium": (-30.3100, 153.1200),
    # QLD
    "Suncorp Stadium": (-27.4649, 153.0095),
    "The Gabba": (-27.4858, 153.0381),
    "Cbus Super Stadium": (-28.0670, 153.3780),
    "Kayo Stadium": (-27.2700, 153.0200),
    "Moreton Daily Stadium": (-27.2700, 153.0200),
    "Queensland Country Bank Stadium": (-19.3160, 146.7620),
    "BB Print Stadium": (-21.1500, 149.1800),
    # VIC
    "AAMI Park": (-37.8250, 144.9830),
    "Marvel Stadium": (-37.8160, 144.9470),
    # ACT
    "GIO Stadium": (-35.2500, 149.1020),
    "Canberra Stadium": (-35.2500, 149.1020),
    # SA / WA / NT / NZ / intl
    "Adelaide Oval": (-34.9150, 138.5960),
    "HBF Park": (-31.9450, 115.8700),
    "Optus Stadium": (-31.9510, 115.8890),
    "TIO Stadium": (-12.3990, 130.8870),
    "Go Media Stadium": (-36.9160, 174.8120),
    "Mt Smart Stadium": (-36.9160, 174.8120),
    "One NZ Stadium": (-43.5400, 172.6400),
    "Allegiant Stadium": (36.0900, -115.1830),
}

# City centre fallbacks when venue name is unknown
CITY_TO_COORDS: dict[str, tuple[float, float]] = {
    "sydney": (-33.8688, 151.2093),
    "brisbane": (-27.4698, 153.0251),
    "melbourne": (-37.8136, 144.9631),
    "newcastle": (-32.9283, 151.7817),
    "canberra": (-35.2809, 149.1300),
    "gold coast": (-28.0167, 153.4000),
    "townsville": (-19.2590, 146.8169),
    "perth": (-31.9505, 115.8605),
    "adelaide": (-34.9285, 138.6007),
    "auckland": (-36.8485, 174.7633),
    "christchurch": (-43.5321, 172.6362),
    "wollongong": (-34.4278, 150.8931),
    "parramatta": (-33.8151, 151.0011),
    "penrith": (-33.7500, 150.7000),
}


def resolve_coords(
    venue: str | None,
    venue_city: str | None = None,
) -> tuple[float, float] | None:
    if venue and venue in VENUE_TO_COORDS:
        return VENUE_TO_COORDS[venue]
    # Case-insensitive venue match
    if venue:
        for name, coords in VENUE_TO_COORDS.items():
            if name.lower() == venue.lower():
                return coords
    if venue_city:
        city = venue_city.strip().lower()
        if city in CITY_TO_COORDS:
            return CITY_TO_COORDS[city]
        for key, coords in CITY_TO_COORDS.items():
            if key in city or city in key:
                return coords
    return None


def geocode_open_meteo(
    client: RateLimitedHttpClient,
    *,
    venue: str | None,
    venue_city: str | None,
) -> tuple[float, float] | None:
    """Soft geocode via Open-Meteo (venue + city, Australia)."""
    query_parts = [p for p in (venue, venue_city, "Australia") if p]
    if not query_parts:
        return None
    params = {
        "name": ", ".join(query_parts[:2]) if venue and venue_city else query_parts[0],
        "count": 1,
        "language": "en",
        "format": "json",
    }
    url = f"https://geocoding-api.open-meteo.com/v1/search?{urlencode(params)}"
    try:
        data = client.get_json(url)
    except Exception as e:
        logger.warning("Open-Meteo geocode failed: %s", e)
        return None
    results = data.get("results") if isinstance(data, dict) else None
    if not results:
        return None
    first = results[0]
    lat, lon = first.get("latitude"), first.get("longitude")
    if lat is None or lon is None:
        return None
    return float(lat), float(lon)


def resolve_coords_with_fallback(
    client: RateLimitedHttpClient | None,
    venue: str | None,
    venue_city: str | None = None,
) -> tuple[float, float] | None:
    coords = resolve_coords(venue, venue_city)
    if coords is not None:
        return coords
    if client is None:
        return None
    return geocode_open_meteo(client, venue=venue, venue_city=venue_city)
