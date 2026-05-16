import re
import logging
from typing import Iterator, Optional

from bs4 import BeautifulSoup

from .fetcher import Fetcher
from .parser import Listing, parse_page

logger = logging.getLogger(__name__)

# Gumtree puts the page number just before the code segment, e.g.:
#   /s-category/location/keywords/k0c123l456r50          (page 1)
#   /s-category/location/keywords/page-2/k0c123l456r50   (page 2+)
_CODE_SEG_RE = re.compile(r"(/k\d[^/]*(?:/|$))")
_PAGE_SEG_RE = re.compile(r"/page-\d+")

_SEL_PAGINATION = "nav[aria-label]"
_SEL_RESULT_COUNT = "[class*='result-count'], [class*='results-count']"


def build_page_url(base_url: str, page: int) -> str:
    # Strip any existing page segment
    clean = _PAGE_SEG_RE.sub("", base_url)

    if page == 1:
        return clean

    match = _CODE_SEG_RE.search(clean)
    if match:
        insert_at = match.start()
        return clean[:insert_at] + f"/page-{page}" + clean[insert_at:]

    # Fallback for URLs without a recognisable code segment
    sep = "&" if "?" in clean else "?"
    return f"{clean}{sep}page={page}"


def detect_total_pages(soup: BeautifulSoup) -> Optional[int]:
    # Try numbered pagination links first
    nav = soup.select_one(_SEL_PAGINATION)
    if nav:
        nums = [
            int(a.get_text(strip=True))
            for a in nav.find_all("a")
            if a.get_text(strip=True).isdigit()
        ]
        if nums:
            return max(nums)

    # Fall back to result count text ("1-25 of 150 results")
    count_el = soup.select_one(_SEL_RESULT_COUNT)
    if count_el:
        text = count_el.get_text()
        m = re.search(r"of\s+([\d,]+)", text)
        if m:
            total = int(m.group(1).replace(",", ""))
            return max(1, -(-total // 25))  # ceiling division, 25 per page

    return None


def iter_pages(
    fetcher: Fetcher,
    base_url: str,
    max_pages: Optional[int] = None,
) -> Iterator[list[Listing]]:
    """
    Yield lists of Listing objects one page at a time.

    Stops when:
    - all known pages have been fetched, or
    - a page returns no listings (layout change or end of results), or
    - max_pages is reached.
    """
    total_pages: Optional[int] = None
    page = 1

    while True:
        if max_pages and page > max_pages:
            logger.info("Reached max_pages limit (%d)", max_pages)
            break

        url = build_page_url(base_url, page)
        logger.info("Fetching page %d: %s", page, url)

        soup = fetcher.get(url)
        if soup is None:
            logger.error("Failed to fetch page %d — stopping pagination", page)
            break

        if page == 1 and total_pages is None:
            total_pages = detect_total_pages(soup)
            if total_pages:
                logger.info("Detected %d total page(s)", total_pages)

        listings = parse_page(soup)
        if not listings:
            logger.info("No listings on page %d — end of results", page)
            break

        yield listings

        if total_pages and page >= total_pages:
            logger.info("Fetched all %d page(s)", total_pages)
            break

        page += 1
