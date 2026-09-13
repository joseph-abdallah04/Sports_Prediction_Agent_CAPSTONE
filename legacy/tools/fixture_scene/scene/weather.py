"""Open-Meteo kickoff-hour forecast for a venue."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from .http_client import RateLimitedHttpClient
from .venues import resolve_coords_with_fallback

logger = logging.getLogger(__name__)

AU_TZ = ZoneInfo("Australia/Sydney")

# WMO weather interpretation codes (Open-Meteo)
_CODE_SUMMARY = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _parse_kickoff(kickoff: str | datetime) -> datetime:
    if isinstance(kickoff, datetime):
        dt = kickoff
    else:
        text = str(kickoff).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=AU_TZ)
    return dt.astimezone(AU_TZ)


def math_weather_label(
    *,
    precipitation_mm: float | None,
    precipitation_probability_pct: float | None,
    weather_code: int | None,
) -> str:
    """Map forecast → Fine / Rain for math engine ctx_weather."""
    rainy_codes = {51, 53, 55, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
    if weather_code is not None and weather_code in rainy_codes:
        return "Rain"
    if precipitation_mm is not None and precipitation_mm >= 0.2:
        return "Rain"
    if precipitation_probability_pct is not None and precipitation_probability_pct >= 50:
        return "Rain"
    if weather_code is not None or precipitation_mm is not None:
        return "Fine"
    return "unknown"


def fetch_kickoff_weather(
    client: RateLimitedHttpClient,
    *,
    venue: str | None,
    venue_city: str | None,
    kickoff: str | datetime,
) -> dict[str, Any]:
    """Return weather block; soft structure with error field on failure."""
    try:
        kick_dt = _parse_kickoff(kickoff)
    except Exception as e:
        return {
            "provider": "open-meteo",
            "at_kickoff": None,
            "math_weather_label": "unknown",
            "source_url": None,
            "error": f"Invalid kickoff: {e}",
        }

    coords = resolve_coords_with_fallback(client, venue, venue_city)
    if coords is None:
        return {
            "provider": "open-meteo",
            "at_kickoff": None,
            "math_weather_label": "unknown",
            "source_url": None,
            "error": f"No coordinates for venue={venue!r} city={venue_city!r}",
        }

    lat, lon = coords
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": (
            "temperature_2m,precipitation,precipitation_probability,"
            "weather_code,wind_speed_10m"
        ),
        "timezone": "Australia/Sydney",
        "forecast_days": 7,
    }
    source_url = f"https://api.open-meteo.com/v1/forecast?{urlencode(params)}"
    try:
        data = client.get_json(source_url)
    except Exception as e:
        logger.warning("Open-Meteo failed: %s", e)
        return {
            "provider": "open-meteo",
            "at_kickoff": None,
            "math_weather_label": "unknown",
            "source_url": source_url,
            "error": str(e),
        }

    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        return {
            "provider": "open-meteo",
            "at_kickoff": None,
            "math_weather_label": "unknown",
            "source_url": source_url,
            "error": "No hourly forecast returned",
        }

    # Pick closest hour to kickoff
    target = kick_dt.replace(minute=0, second=0, microsecond=0)
    best_i = 0
    best_delta = None
    for i, t in enumerate(times):
        try:
            ht = datetime.fromisoformat(t)
            if ht.tzinfo is None:
                ht = ht.replace(tzinfo=AU_TZ)
            delta = abs((ht - target).total_seconds())
        except ValueError:
            continue
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_i = i

    def _at(key: str):
        arr = hourly.get(key) or []
        return arr[best_i] if best_i < len(arr) else None

    temp = _at("temperature_2m")
    precip = _at("precipitation")
    precip_prob = _at("precipitation_probability")
    code = _at("weather_code")
    wind = _at("wind_speed_10m")
    code_i = int(code) if code is not None else None

    at_kickoff = {
        "time_local": times[best_i],
        "temperature_c": temp,
        "precipitation_mm": precip,
        "precipitation_probability_pct": precip_prob,
        "wind_speed_kmh": wind,
        "weather_code": code_i,
        "summary": _CODE_SUMMARY.get(code_i if code_i is not None else -1, "Unknown"),
        "latitude": lat,
        "longitude": lon,
        "venue": venue,
        "venue_city": venue_city,
    }
    label = math_weather_label(
        precipitation_mm=float(precip) if precip is not None else None,
        precipitation_probability_pct=float(precip_prob) if precip_prob is not None else None,
        weather_code=code_i,
    )
    return {
        "provider": "open-meteo",
        "at_kickoff": at_kickoff,
        "math_weather_label": label,
        "source_url": source_url,
        "error": None,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
