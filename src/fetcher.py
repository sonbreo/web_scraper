import logging
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class Fetcher:
    def __init__(self, config: dict):
        http = config["http"]
        self._delay = http["request_delay"]
        self._timeout = http["timeout"]
        self._max_retries = http["max_retries"]
        self._last_request_at: float = 0.0

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": _USER_AGENT})

        proxies = http.get("proxies")
        if proxies:
            self._session.proxies.update(proxies)

    def get(self, url: str) -> Optional[BeautifulSoup]:
        self._rate_limit()

        for attempt in range(1, self._max_retries + 2):
            try:
                response = self._session.get(url, timeout=self._timeout)
                self._last_request_at = time.monotonic()

                if response.status_code == 200:
                    return BeautifulSoup(response.content, "lxml")

                if 400 <= response.status_code < 500:
                    logger.error("Client error %s for %s — not retrying", response.status_code, url)
                    return None

                # 5xx — retryable
                logger.warning("Server error %s for %s (attempt %d)", response.status_code, url, attempt)

            except requests.exceptions.Timeout:
                logger.warning("Timeout fetching %s (attempt %d)", url, attempt)
            except requests.exceptions.ConnectionError:
                logger.warning("Connection error fetching %s (attempt %d)", url, attempt)
            except requests.exceptions.RequestException as exc:
                logger.error("Unexpected request error for %s: %s", url, exc)
                return None

            if attempt <= self._max_retries:
                backoff = 2 ** attempt
                logger.info("Retrying in %ds...", backoff)
                time.sleep(backoff)

        logger.error("All %d attempts failed for %s", self._max_retries + 1, url)
        return None

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait = self._delay - elapsed
        if wait > 0:
            logger.debug("Rate limiting: sleeping %.2fs", wait)
            time.sleep(wait)

    def close(self) -> None:
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
