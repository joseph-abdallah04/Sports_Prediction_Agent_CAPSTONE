"""Job A: one-off historical backfill orchestrator.

Discovers every completed NRL Premiership match from the draw pages,
scrapes each match centre's raw JSON payload, and stores it (untouched)
in the raw data lake. The run is resumable: progress is tracked in a
manifest, so re-running after an interruption continues where it left off.

Usage:
    uv run python -m historical_data_backfill_etl.backfill \
        --start-season 2015 --end-season 2026

Useful flags for test runs:
    --discover-only      only build the URL manifest, don't scrape matches
    --limit N            stop after scraping N matches this run
    --delay SECONDS      seconds between requests (default 1.0)
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from nrl_scraping.http import NRLHttpClient
from nrl_scraping.match_scraper import extract_match_data, get_match_id

from .draw_scraper import discover_season

logger = logging.getLogger("backfill")

ENGINE_ROOT = Path(__file__).resolve().parents[1]
DATA_LAKE_DIR = ENGINE_ROOT / "data_lake"
RAW_HISTORICAL_DIR = DATA_LAKE_DIR / "raw_historical"
MANIFESTS_DIR = DATA_LAKE_DIR / "manifests"
MANIFEST_PATH = MANIFESTS_DIR / "backfill_manifest.json"
FAILURES_PATH = MANIFESTS_DIR / "failures.json"

MANIFEST_SAVE_EVERY = 10  # matches scraped between manifest checkpoint saves


def load_json(path: Path, default):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


def record_failure(url: str, stage: str, error: Exception) -> None:
    failures = load_json(FAILURES_PATH, default=[])
    failures.append(
        {
            "url": url,
            "stage": stage,
            "error": f"{type(error).__name__}: {error}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    save_json(FAILURES_PATH, failures)


def run_discovery(client: NRLHttpClient, manifest: dict, seasons: list[int]) -> None:
    """Populate the manifest with match URLs for any undiscovered seasons."""
    for season in seasons:
        if str(season) in manifest["seasons_discovered"]:
            logger.info("Season %d already discovered, skipping", season)
            continue

        logger.info("Discovering season %d...", season)
        try:
            fixtures = discover_season(client, season)
        except Exception as e:
            logger.error("Discovery failed for season %d: %s", season, e)
            record_failure(f"season={season}", "discovery", e)
            continue

        for fixture in fixtures:
            url = fixture["match_centre_url"]
            if url not in manifest["matches"]:
                fixture["status"] = "pending"
                manifest["matches"][url] = fixture

        manifest["seasons_discovered"].append(str(season))
        save_json(MANIFEST_PATH, manifest)
        logger.info("Season %d: %d completed matches discovered", season, len(fixtures))


def run_extraction(client: NRLHttpClient, manifest: dict, limit: int | None) -> dict:
    """Scrape every pending match in the manifest into the raw data lake."""
    pending = [
        (url, meta)
        for url, meta in manifest["matches"].items()
        if meta["status"] != "done"
    ]
    pending.sort(key=lambda item: (item[1]["season"], item[1]["round_number"]))

    stats = {"scraped": 0, "failed": 0, "skipped_existing": 0}
    total = len(pending) if limit is None else min(limit, len(pending))
    logger.info("%d matches pending extraction (processing %d this run)", len(pending), total)

    started = time.monotonic()
    for i, (url, meta) in enumerate(pending):
        if limit is not None and stats["scraped"] + stats["failed"] >= limit:
            break

        try:
            payload = extract_match_data(client, url)
            match_id = get_match_id(payload)
        except Exception as e:
            logger.error("Failed to scrape %s: %s", url, e)
            meta["status"] = "failed"
            record_failure(url, "extraction", e)
            stats["failed"] += 1
            continue

        season_dir = RAW_HISTORICAL_DIR / str(meta["season"])
        season_dir.mkdir(parents=True, exist_ok=True)
        out_path = season_dir / f"nrl_match_{match_id}.json"
        save_json(out_path, payload)

        meta["status"] = "done"
        meta["match_id"] = match_id
        meta["file"] = str(out_path.relative_to(ENGINE_ROOT))
        stats["scraped"] += 1

        done_count = stats["scraped"] + stats["failed"]
        if done_count % MANIFEST_SAVE_EVERY == 0:
            save_json(MANIFEST_PATH, manifest)
            rate = stats["scraped"] / (time.monotonic() - started)
            remaining = total - done_count
            eta_min = (remaining / rate / 60) if rate > 0 else 0
            logger.info(
                "Progress: %d/%d scraped (%.1f/min, ~%.0f min remaining)",
                done_count, total, rate * 60, eta_min,
            )

    save_json(MANIFEST_PATH, manifest)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="NRL historical backfill (Job A)")
    parser.add_argument("--start-season", type=int, default=2015)
    parser.add_argument("--end-season", type=int, default=2026)
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    parser.add_argument("--discover-only", action="store_true", help="build manifest only")
    parser.add_argument("--limit", type=int, default=None, help="max matches to scrape this run")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    client = NRLHttpClient(delay_seconds=args.delay)
    manifest = load_json(
        MANIFEST_PATH, default={"seasons_discovered": [], "matches": {}}
    )

    seasons = list(range(args.start_season, args.end_season + 1))
    run_discovery(client, manifest, seasons)

    total_discovered = len(manifest["matches"])
    logger.info("Manifest contains %d matches total", total_discovered)

    if args.discover_only:
        logger.info("Discover-only mode: stopping before extraction")
        return 0

    stats = run_extraction(client, manifest, args.limit)

    done = sum(1 for m in manifest["matches"].values() if m["status"] == "done")
    logger.info(
        "Run complete: %d scraped, %d failed, %d/%d matches in data lake",
        stats["scraped"], stats["failed"], done, total_discovered,
    )
    if stats["failed"] > 0:
        logger.warning("Failures were logged to %s", FAILURES_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
