"""Post-run operator summary for the weekly ETL."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from feature_engineering.build_dataset import DATASET_PATH
from model import METRICS_PATH

ENGINE_ROOT = Path(__file__).resolve().parents[1]
RAW_HISTORICAL_DIR = ENGINE_ROOT / "data_lake" / "raw_historical"
MANIFESTS_DIR = ENGINE_ROOT / "data_lake" / "manifests"
LAST_RUN_PATH = MANIFESTS_DIR / "weekly_last_run.json"


@dataclass
class RunSummary:
    season: int
    pending_found: int
    skipped_known_urls: int
    scraped: int
    failed: int
    skipped_existing_ids: int
    raw_json_count_season: int
    training_rows: int | None
    trained_at: str | None
    dry_run: bool
    scrape_only: bool
    skip_scrape: bool


def count_raw_json(season: int) -> int:
    season_dir = RAW_HISTORICAL_DIR / str(season)
    if not season_dir.exists():
        return 0
    return len(list(season_dir.glob("nrl_match_*.json")))


def training_row_count() -> int | None:
    if not DATASET_PATH.exists():
        return None
    import pandas as pd
    return int(len(pd.read_parquet(DATASET_PATH)))


def trained_at() -> str | None:
    if not METRICS_PATH.exists():
        return None
    with open(METRICS_PATH, encoding="utf-8") as f:
        return json.load(f).get("trained_at")


def print_summary(summary: RunSummary) -> None:
    print("\n=== Weekly ETL complete ===")
    print(f"  Season scanned:          {summary.season}")
    if summary.dry_run:
        print("  Mode:                    dry-run (no writes)")
    elif summary.scrape_only:
        print("  Mode:                    scrape-only")
    elif summary.skip_scrape:
        print("  Mode:                    skip-scrape (rebuild + retrain)")
    print(f"  Pending on draw:         {summary.pending_found}")
    print(f"  Skipped (known URL):     {summary.skipped_known_urls}")
    print(f"  New matches scraped:   {summary.scraped}")
    print(f"  Skipped (ID on disk):    {summary.skipped_existing_ids}")
    print(f"  Scrape failures:         {summary.failed}")
    print(f"  Raw JSON total (season): {summary.raw_json_count_season}")
    if summary.training_rows is not None:
        print(f"  Training rows:           {summary.training_rows}")
    if summary.trained_at:
        print(f"  Model retrained at:      {summary.trained_at}")
    if not summary.dry_run and not summary.scrape_only:
        print("  Next step:               model.predict (or Phase 4 API)")


def write_last_run(summary: RunSummary) -> None:
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        **summary.__dict__,
    }
    with open(LAST_RUN_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
