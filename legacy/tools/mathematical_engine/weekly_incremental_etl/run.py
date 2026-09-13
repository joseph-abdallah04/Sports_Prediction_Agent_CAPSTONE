"""Job B orchestrator: weekly incremental ETL.

Discovers newly completed matches on nrl.com, scrapes only those missing from
the raw data lake, full-rebuilds the feature store, and retrains the model.

Usage:
    uv run python -m weekly_incremental_etl.run
    uv run python -m weekly_incremental_etl.run --season 2026
    uv run python -m weekly_incremental_etl.run --dry-run
    uv run python -m weekly_incremental_etl.run --scrape-only
    uv run python -m weekly_incremental_etl.run --skip-scrape
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from feature_engineering.build_dataset import DATASET_PATH, FEATURE_STORE_DIR, build
from model.train import train_production
from nrl_scraping.http import NRLHttpClient

from .discover import WEEKLY_MANIFEST_PATH, discover_pending
from .report import RunSummary, count_raw_json, print_summary, trained_at, training_row_count, write_last_run
from .scrape import scrape_pending

logger = logging.getLogger("weekly_etl")


def _append_run_record(summary: RunSummary) -> None:
    if WEEKLY_MANIFEST_PATH.exists():
        with open(WEEKLY_MANIFEST_PATH, encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {"runs": [], "scraped_urls": {}}

    manifest.setdefault("runs", []).append(
        {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            **summary.__dict__,
        }
    )
    WEEKLY_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = WEEKLY_MANIFEST_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    tmp.replace(WEEKLY_MANIFEST_PATH)


def rebuild_features() -> int:
    """Full Stage 1 + 2 rebuild (DD-15). Returns training row count."""
    logger.info("Rebuilding feature store (full flatten + dataset)...")
    FEATURE_STORE_DIR.mkdir(parents=True, exist_ok=True)
    dataset = build(min_history=0, reflatten=True)
    dataset.to_parquet(DATASET_PATH, index=False)
    logger.info("Wrote %d rows to %s", len(dataset), DATASET_PATH)
    return len(dataset)


def retrain_model() -> int:
    """Retrain production model with saved hyperparameters."""
    logger.info("Retraining production model...")
    return train_production()


def run_pipeline(
    season: int,
    *,
    dry_run: bool = False,
    scrape_only: bool = False,
    skip_scrape: bool = False,
    delay: float = 1.0,
) -> int:
    client = NRLHttpClient(delay_seconds=delay)

    pending, skipped_urls = discover_pending(client, season)
    scrape_stats = scrape_pending(client, pending, dry_run=dry_run) if not skip_scrape else None

    if dry_run:
        print("\n=== Dry run — would scrape these matches ===")
        for fx in pending:
            print(f"  Round {fx.round_number}: {fx.home_team} v {fx.away_team}")
            print(f"    {fx.match_centre_url}")
        summary = RunSummary(
            season=season,
            pending_found=len(pending),
            skipped_known_urls=skipped_urls,
            scraped=0,
            failed=0,
            skipped_existing_ids=0,
            raw_json_count_season=count_raw_json(season),
            training_rows=training_row_count(),
            trained_at=trained_at(),
            dry_run=True,
            scrape_only=False,
            skip_scrape=skip_scrape,
        )
        print_summary(summary)
        return 0

    if scrape_only:
        summary = RunSummary(
            season=season,
            pending_found=len(pending),
            skipped_known_urls=skipped_urls,
            scraped=scrape_stats.scraped,
            failed=scrape_stats.failed,
            skipped_existing_ids=scrape_stats.skipped_existing,
            raw_json_count_season=count_raw_json(season),
            training_rows=training_row_count(),
            trained_at=trained_at(),
            dry_run=False,
            scrape_only=True,
            skip_scrape=False,
        )
        print_summary(summary)
        write_last_run(summary)
        _append_run_record(summary)
        return 1 if scrape_stats.failed else 0

    rebuild_features()
    train_rc = retrain_model()

    summary = RunSummary(
        season=season,
        pending_found=len(pending) if not skip_scrape else 0,
        skipped_known_urls=skipped_urls if not skip_scrape else 0,
        scraped=scrape_stats.scraped if scrape_stats else 0,
        failed=scrape_stats.failed if scrape_stats else 0,
        skipped_existing_ids=scrape_stats.skipped_existing if scrape_stats else 0,
        raw_json_count_season=count_raw_json(season),
        training_rows=training_row_count(),
        trained_at=trained_at(),
        dry_run=False,
        scrape_only=False,
        skip_scrape=skip_scrape,
    )
    print_summary(summary)
    write_last_run(summary)
    _append_run_record(summary)

    if scrape_stats and scrape_stats.failed:
        logger.warning("Some scrapes failed — see data_lake/manifests/weekly_failures.json")
    return train_rc


def main() -> int:
    parser = argparse.ArgumentParser(description="Weekly incremental ETL (Job B)")
    parser.add_argument(
        "--season", type=int, default=datetime.now().year,
        help="season to scan for new completed matches (default: current year)",
    )
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between HTTP requests")
    parser.add_argument("--dry-run", action="store_true", help="list pending matches only")
    parser.add_argument("--scrape-only", action="store_true", help="scrape new JSON only")
    parser.add_argument("--skip-scrape", action="store_true", help="rebuild features + retrain only")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.scrape_only and args.skip_scrape:
        parser.error("--scrape-only and --skip-scrape are mutually exclusive")

    return run_pipeline(
        args.season,
        dry_run=args.dry_run,
        scrape_only=args.scrape_only,
        skip_scrape=args.skip_scrape,
        delay=args.delay,
    )


if __name__ == "__main__":
    sys.exit(main())
