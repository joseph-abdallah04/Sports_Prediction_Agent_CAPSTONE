"""Scrape pending fixtures into the raw data lake."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from nrl_scraping.http import NRLHttpClient
from nrl_scraping.match_scraper import extract_match_data, get_match_id

from .discover import PendingFixture, WEEKLY_MANIFEST_PATH, on_disk_match_ids

logger = logging.getLogger(__name__)

ENGINE_ROOT = Path(__file__).resolve().parents[1]
DATA_LAKE_DIR = ENGINE_ROOT / "data_lake"
RAW_HISTORICAL_DIR = DATA_LAKE_DIR / "raw_historical"
MANIFESTS_DIR = DATA_LAKE_DIR / "manifests"
FAILURES_PATH = MANIFESTS_DIR / "weekly_failures.json"


@dataclass
class ScrapeStats:
    scraped: int = 0
    failed: int = 0
    skipped_existing: int = 0


def _load_json(path: Path, default):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


def _record_failure(url: str, error: Exception) -> None:
    failures = _load_json(FAILURES_PATH, default=[])
    failures.append(
        {
            "url": url,
            "error": f"{type(error).__name__}: {error}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    _save_json(FAILURES_PATH, failures)


def scrape_pending(
    client: NRLHttpClient,
    pending: list[PendingFixture],
    *,
    dry_run: bool = False,
) -> ScrapeStats:
    """Download raw JSON for each pending fixture. Skips duplicate match IDs."""
    stats = ScrapeStats()
    if dry_run or not pending:
        return stats

    manifest = _load_json(WEEKLY_MANIFEST_PATH, default={"runs": [], "scraped_urls": {}})
    scraped_urls = manifest.setdefault("scraped_urls", {})

    for fixture in pending:
        season = fixture.season
        existing_ids = on_disk_match_ids(season)

        try:
            payload = extract_match_data(client, fixture.match_centre_url)
            match_id = get_match_id(payload)
        except Exception as e:
            logger.error("Failed to scrape %s: %s", fixture.match_centre_url, e)
            _record_failure(fixture.match_centre_url, e)
            stats.failed += 1
            continue

        if match_id in existing_ids:
            logger.info(
                "Match %s already on disk (%s v %s) — skipping write",
                match_id, fixture.home_team, fixture.away_team,
            )
            stats.skipped_existing += 1
            scraped_urls[fixture.match_centre_url] = {
                "match_id": match_id,
                "season": season,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "note": "already_on_disk",
            }
            continue

        season_dir = RAW_HISTORICAL_DIR / str(season)
        season_dir.mkdir(parents=True, exist_ok=True)
        out_path = season_dir / f"nrl_match_{match_id}.json"
        _save_json(out_path, payload)

        scraped_urls[fixture.match_centre_url] = {
            "match_id": match_id,
            "season": season,
            "file": str(out_path.relative_to(ENGINE_ROOT)),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        stats.scraped += 1
        logger.info(
            "Scraped %s v %s (round %d) -> %s",
            fixture.home_team, fixture.away_team, fixture.round_number, out_path.name,
        )

    _save_json(WEEKLY_MANIFEST_PATH, manifest)
    return stats
