"""Discover completed fixtures that are not yet in the raw data lake."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from historical_data_backfill_etl.draw_scraper import discover_season
from nrl_scraping.http import NRLHttpClient

logger = logging.getLogger(__name__)

ENGINE_ROOT = Path(__file__).resolve().parents[1]
DATA_LAKE_DIR = ENGINE_ROOT / "data_lake"
RAW_HISTORICAL_DIR = DATA_LAKE_DIR / "raw_historical"
MANIFESTS_DIR = DATA_LAKE_DIR / "manifests"
BACKFILL_MANIFEST_PATH = MANIFESTS_DIR / "backfill_manifest.json"
WEEKLY_MANIFEST_PATH = MANIFESTS_DIR / "weekly_manifest.json"


@dataclass(frozen=True)
class PendingFixture:
    match_centre_url: str
    season: int
    round_number: int
    round_title: str
    home_team: str
    away_team: str


def _load_json(path: Path, default):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def on_disk_match_ids(season: int) -> set[str]:
    """Match IDs already present as raw JSON files for this season."""
    season_dir = RAW_HISTORICAL_DIR / str(season)
    if not season_dir.exists():
        return set()
    return {p.stem.removeprefix("nrl_match_") for p in season_dir.glob("nrl_match_*.json")}


def known_urls_for_season(season: int) -> set[str]:
    """URLs we have already scraped (backfill manifest + weekly manifest)."""
    urls: set[str] = set()

    backfill = _load_json(BACKFILL_MANIFEST_PATH, default={"matches": {}})
    for url, meta in backfill.get("matches", {}).items():
        if meta.get("season") == season and meta.get("status") == "done":
            urls.add(url)

    weekly = _load_json(WEEKLY_MANIFEST_PATH, default={"scraped_urls": {}})
    for url, meta in weekly.get("scraped_urls", {}).items():
        if meta.get("season") == season:
            urls.add(url)

    return urls


def discover_pending(client: NRLHttpClient, season: int) -> tuple[list[PendingFixture], int]:
    """Return fixtures to scrape and how many were skipped as already on disk."""
    logger.info("Discovering completed matches for season %d...", season)
    fixtures = discover_season(client, season)
    known_urls = known_urls_for_season(season)

    pending: list[PendingFixture] = []
    skipped = 0
    for fixture in fixtures:
        url = fixture["match_centre_url"]
        if url in known_urls:
            skipped += 1
            continue
        pending.append(
            PendingFixture(
                match_centre_url=url,
                season=fixture["season"],
                round_number=fixture["round_number"],
                round_title=fixture.get("round_title", ""),
                home_team=fixture.get("home_team", ""),
                away_team=fixture.get("away_team", ""),
            )
        )

    logger.info(
        "Season %d: %d completed on draw, %d already scraped, %d pending",
        season, len(fixtures), skipped, len(pending),
    )
    return pending, skipped
