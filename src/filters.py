import re
import logging
from typing import Optional

from .parser import Listing

logger = logging.getLogger(__name__)

# Matches Gumtree age strings: "3 hours ago", "2 days ago", "1 week ago", etc.
_AGE_RE = re.compile(r"(\d+)\s*(minute|hour|day|week|month|year)", re.IGNORECASE)

_UNIT_TO_DAYS: dict[str, float] = {
    "minute": 1 / 1440,
    "hour": 1 / 24,
    "day": 1.0,
    "week": 7.0,
    "month": 30.0,
    "year": 365.0,
}


def apply_filters(
    listings: list[Listing],
    filters: dict,
    keywords: Optional[list[str]] = None,
) -> list[Listing]:
    kept = [l for l in listings if _passes(l, filters, keywords)]
    logger.info("Filtering: kept %d of %d listings", len(kept), len(listings))
    return kept


def _passes(
    listing: Listing,
    filters: dict,
    keywords: Optional[list[str]],
) -> bool:
    # --- keyword match (all keywords must appear in title) ---
    if keywords:
        title_lower = listing.title.lower()
        if not all(kw.lower() in title_lower for kw in keywords):
            logger.debug("Dropped (keyword): %s", listing.title)
            return False

    # --- price range ---
    price_cfg = filters.get("price", {})
    price_min = price_cfg.get("min")
    price_max = price_cfg.get("max")
    if listing.price is not None:
        if price_min is not None and listing.price < price_min:
            logger.debug("Dropped (price low %s): %s", listing.price, listing.title)
            return False
        if price_max is not None and listing.price > price_max:
            logger.debug("Dropped (price high %s): %s", listing.price, listing.title)
            return False

    # --- exclude keywords ---
    exclude = [kw.lower() for kw in filters.get("exclude_keywords", [])]
    if exclude:
        title_lower = listing.title.lower()
        for kw in exclude:
            if kw in title_lower:
                logger.debug("Dropped (excluded kw '%s'): %s", kw, listing.title)
                return False

    # --- seller type ---
    seller_type_cfg = filters.get("seller_type", "all")
    if seller_type_cfg != "all" and listing.seller_type not in ("unknown", seller_type_cfg):
        logger.debug(
            "Dropped (seller_type '%s' != '%s'): %s",
            listing.seller_type, seller_type_cfg, listing.title,
        )
        return False

    # --- age / date filter ---
    max_age_days = filters.get("max_age_days")
    if max_age_days is not None and listing.date_raw:
        age = _parse_age_days(listing.date_raw)
        if age is not None and age > max_age_days:
            logger.debug(
                "Dropped (age %.1f > %s days): %s", age, max_age_days, listing.title
            )
            return False

    # --- location substring filter ---
    location_filter = filters.get("location")
    if location_filter and listing.location:
        if location_filter.lower() not in listing.location.lower():
            logger.debug(
                "Dropped (location '%s' not in '%s'): %s",
                location_filter, listing.location, listing.title,
            )
            return False

    return True


def _parse_age_days(date_raw: str) -> Optional[float]:
    match = _AGE_RE.search(date_raw)
    if not match:
        return None
    n = int(match.group(1))
    unit = match.group(2).lower()
    return n * _UNIT_TO_DAYS.get(unit, 1.0)
