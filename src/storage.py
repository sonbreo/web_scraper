import csv
import json
import logging
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .parser import Listing

logger = logging.getLogger(__name__)

_OUTPUT_DIR = Path(__file__).parent.parent / "output"
_FIELDS = [
    "listing_id", "title", "price", "price_raw",
    "url", "location", "date_raw", "thumbnail_url", "seller_type",
]


def save(listings: list[Listing], config: dict) -> None:
    if not listings:
        logger.info("No listings to save")
        return
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_cfg = config.get("features", {}).get("output", {})
    if output_cfg.get("csv", True):
        _save_csv(listings)
    if output_cfg.get("json", False):
        _save_json(listings)
    if output_cfg.get("sqlite", False):
        _save_sqlite(listings)


def _save_csv(listings: list[Listing]) -> None:
    path = _OUTPUT_DIR / "listings.csv"
    write_header = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        if write_header:
            writer.writeheader()
        for listing in listings:
            writer.writerow({k: getattr(listing, k) for k in _FIELDS})
    logger.info("CSV: wrote %d rows to %s", len(listings), path)


def _save_json(listings: list[Listing]) -> None:
    path = _OUTPUT_DIR / "listings.json"
    existing: list[dict] = []
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception as exc:
            logger.warning("Could not read existing JSON file, overwriting: %s", exc)
    existing.extend(asdict(l) for l in listings)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    logger.info("JSON: wrote %d total records to %s", len(existing), path)


def _save_sqlite(listings: list[Listing]) -> None:
    path = _OUTPUT_DIR / "listings.db"
    with sqlite3.connect(path) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS listings (
                {', '.join(f'{f} TEXT' for f in _FIELDS)},
                PRIMARY KEY (listing_id)
            )
        """)
        rows = [tuple(getattr(l, f) for f in _FIELDS) for l in listings]
        conn.executemany(
            f"INSERT OR IGNORE INTO listings ({', '.join(_FIELDS)}) "
            f"VALUES ({', '.join('?' * len(_FIELDS))})",
            rows,
        )
        conn.commit()
    logger.info("SQLite: inserted up to %d rows into %s", len(listings), path)
