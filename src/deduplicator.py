import json
import logging
from pathlib import Path

from .parser import Listing

logger = logging.getLogger(__name__)

_DEFAULT_STATE_PATH = Path(__file__).parent.parent / "output" / "seen_listings.json"


class Deduplicator:
    def __init__(self, state_path: Path = _DEFAULT_STATE_PATH) -> None:
        self._path = state_path
        self._seen: set[str] = self._load()

    def filter_new(self, listings: list[Listing]) -> list[Listing]:
        new = [l for l in listings if l.listing_id not in self._seen]
        logger.info("Deduplication: %d new of %d listings", len(new), len(listings))
        return new

    def mark_seen(self, listings: list[Listing]) -> None:
        for l in listings:
            self._seen.add(l.listing_id)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(sorted(self._seen), f)
        logger.debug("Saved %d seen listing IDs to %s", len(self._seen), self._path)

    def _load(self) -> set[str]:
        if not self._path.exists():
            return set()
        try:
            with open(self._path) as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("expected a JSON list")
            return set(data)
        except Exception as exc:
            logger.warning("Could not load seen-listings state from %s: %s", self._path, exc)
            return set()
