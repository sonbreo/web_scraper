import logging
import time
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)


def run_once(job: Callable[[], None]) -> None:
    logger.info("Run started at %s", datetime.now().isoformat(timespec="seconds"))
    job()
    logger.info("Run finished at %s", datetime.now().isoformat(timespec="seconds"))


def run_loop(job: Callable[[], None], interval_seconds: float) -> None:
    logger.info(
        "Polling mode: running every %.0f seconds. Press Ctrl+C to stop.", interval_seconds
    )
    while True:
        start = time.monotonic()
        logger.info("Run started at %s", datetime.now().isoformat(timespec="seconds"))
        try:
            job()
        except Exception as exc:
            logger.error("Job failed: %s", exc)
        elapsed = time.monotonic() - start
        logger.info("Run finished in %.1fs", elapsed)
        sleep_for = max(0.0, interval_seconds - elapsed)
        logger.info("Next run in %.0f seconds", sleep_for)
        time.sleep(sleep_for)
