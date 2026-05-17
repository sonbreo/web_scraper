"""
Entry point: ties all modules together for one scrape run.

Accepts config overrides from CLI args (built by cli.py) and runs:
  fetch → parse → filter → deduplicate → store → notify
"""
import logging
from pathlib import Path

from .config import load as load_config
from .deduplicator import Deduplicator
from .fetcher import Fetcher
from .filters import apply_filters
from .notifications import notify
from .pagination import iter_pages
from .parser import parse_page, Listing
from .storage import save

logger = logging.getLogger(__name__)


def run(config: dict, dry_run: bool = False) -> list[Listing]:
    dedup = Deduplicator()
    all_new: list[Listing] = []

    with Fetcher(config) as fetcher:
        for search in config["searches"]:
            url = search["url"]
            keywords = search.get("keywords")
            logger.info("Starting search: %s", url)

            raw_listings: list[Listing] = []
            for page_soup in iter_pages(fetcher, url):
                raw_listings.extend(parse_page(page_soup))

            filtered = apply_filters(raw_listings, config["filters"], keywords=keywords)
            new = dedup.filter_new(filtered)
            dedup.mark_seen(new)
            all_new.extend(new)
            logger.info("Search done: %d new listings after dedup", len(new))

    if dry_run:
        _print_results(all_new)
    else:
        save(all_new, config)
        notify(all_new, config)
        dedup.save()

    return all_new


def _print_results(listings: list[Listing]) -> None:
    if not listings:
        print("No new listings found.")
        return
    print(f"\n{'='*60}")
    print(f"  {len(listings)} new listing(s) found (dry run — not saved)")
    print(f"{'='*60}")
    for l in listings:
        print(f"\n  {l.title}")
        print(f"  Price:    {l.price_raw}")
        print(f"  Location: {l.location or 'N/A'}")
        print(f"  Posted:   {l.date_raw or 'N/A'}")
        print(f"  Seller:   {l.seller_type}")
        print(f"  URL:      {l.url}")
    print()
