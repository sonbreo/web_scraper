import re
import logging
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# CSS selectors — update here if Gumtree changes its markup
_SEL_ITEM = "li.user-ad-row-new-design"
_SEL_TITLE = "span.user-ad-row-new-design__title-span"
_SEL_PRICE = "span.user-ad-price-new-design__price"
_SEL_LOCATION = "span.user-ad-row-new-design__location"
_SEL_AGE = "p.user-ad-row-new-design__age"
_SEL_LINK = "a.user-ad-row-new-design__click-area"
_SEL_THUMB = "img.user-ad-row-new-design__image"
_SEL_SELLER_BADGE = "span.user-ad-badge-new-design__text"

_GUMTREE_BASE = "https://www.gumtree.com.au"

# Matches price strings like "$250", "$1,200"
_PRICE_RE = re.compile(r"\$\s*([\d,]+)")


@dataclass
class Listing:
    listing_id: str
    title: str
    price: Optional[int]     # None when price is non-numeric
    price_raw: str
    url: str
    location: Optional[str]
    date_raw: Optional[str]
    thumbnail_url: Optional[str]
    seller_type: str          # "private", "dealer", or "unknown"


def parse_page(soup: BeautifulSoup) -> list[Listing]:
    items = soup.select(_SEL_ITEM)
    if not items:
        logger.warning(
            "No listing elements found with selector '%s' — "
            "Gumtree markup may have changed",
            _SEL_ITEM,
        )
        return []

    listings: list[Listing] = []
    for item in items:
        try:
            listing = _parse_item(item)
            if listing:
                listings.append(listing)
        except Exception as exc:
            logger.warning("Skipping unparseable listing: %s", exc)

    logger.debug("Parsed %d listings from page", len(listings))
    return listings


def _parse_item(item: Tag) -> Optional[Listing]:
    title_el = item.select_one(_SEL_TITLE)
    if not title_el:
        return None
    title = title_el.get_text(strip=True)

    link_el = item.select_one(_SEL_LINK)
    href = link_el.get("href", "") if link_el else ""
    url = href if href.startswith("http") else _GUMTREE_BASE + href
    listing_id = _extract_id(url)

    price_el = item.select_one(_SEL_PRICE)
    price_raw = price_el.get_text(strip=True) if price_el else ""
    price = _parse_price(price_raw)

    location_el = item.select_one(_SEL_LOCATION)
    location = location_el.get_text(strip=True) if location_el else None

    age_el = item.select_one(_SEL_AGE)
    date_raw = age_el.get_text(strip=True) if age_el else None

    thumb_el = item.select_one(_SEL_THUMB)
    thumbnail_url = thumb_el.get("src") or thumb_el.get("data-src") if thumb_el else None

    badge_el = item.select_one(_SEL_SELLER_BADGE)
    seller_type = _parse_seller_type(badge_el.get_text(strip=True) if badge_el else "")

    return Listing(
        listing_id=listing_id,
        title=title,
        price=price,
        price_raw=price_raw,
        url=url,
        location=location,
        date_raw=date_raw,
        thumbnail_url=thumbnail_url,
        seller_type=seller_type,
    )


def _parse_price(raw: str) -> Optional[int]:
    match = _PRICE_RE.search(raw)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def _extract_id(url: str) -> str:
    # Gumtree listing URLs end with a numeric ID: /q-title/1234567890
    match = re.search(r"/(\d{8,})(?:[/?#]|$)", url)
    return match.group(1) if match else url


def _parse_seller_type(badge_text: str) -> str:
    lower = badge_text.lower()
    if "dealer" in lower or "business" in lower or "trade" in lower:
        return "dealer"
    if "private" in lower:
        return "private"
    return "unknown"
