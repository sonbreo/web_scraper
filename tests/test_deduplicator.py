import json
import pytest
from pathlib import Path
from src.deduplicator import Deduplicator
from src.parser import Listing


def _listing(listing_id: str) -> Listing:
    return Listing(
        listing_id=listing_id,
        title="Test Listing",
        price=100,
        price_raw="$100",
        url=f"https://www.gumtree.com.au/s-ad/{listing_id}",
        location="Melbourne, VIC",
        date_raw="1 day ago",
        thumbnail_url=None,
        seller_type="private",
    )


@pytest.fixture
def state_file(tmp_path):
    return tmp_path / "seen.json"


class TestFilterNew:
    def test_all_new_when_no_state(self, state_file):
        d = Deduplicator(state_file)
        listings = [_listing("111"), _listing("222")]
        assert d.filter_new(listings) == listings

    def test_seen_ids_excluded(self, state_file):
        state_file.write_text(json.dumps(["111"]))
        d = Deduplicator(state_file)
        listings = [_listing("111"), _listing("222")]
        result = d.filter_new(listings)
        assert len(result) == 1
        assert result[0].listing_id == "222"

    def test_all_seen_returns_empty(self, state_file):
        state_file.write_text(json.dumps(["111", "222"]))
        d = Deduplicator(state_file)
        assert d.filter_new([_listing("111"), _listing("222")]) == []

    def test_empty_input(self, state_file):
        d = Deduplicator(state_file)
        assert d.filter_new([]) == []


class TestMarkSeen:
    def test_mark_then_filter(self, state_file):
        d = Deduplicator(state_file)
        listings = [_listing("111"), _listing("222")]
        d.mark_seen(listings)
        assert d.filter_new(listings) == []

    def test_mark_is_idempotent(self, state_file):
        d = Deduplicator(state_file)
        listing = _listing("111")
        d.mark_seen([listing])
        d.mark_seen([listing])
        assert d.filter_new([listing]) == []


class TestPersistence:
    def test_save_and_reload(self, state_file):
        d = Deduplicator(state_file)
        d.mark_seen([_listing("111"), _listing("222")])
        d.save()

        d2 = Deduplicator(state_file)
        assert d2.filter_new([_listing("111"), _listing("222")]) == []
        assert len(d2.filter_new([_listing("333")])) == 1

    def test_save_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "a" / "b" / "seen.json"
        d = Deduplicator(nested)
        d.mark_seen([_listing("111")])
        d.save()
        assert nested.exists()
        assert json.loads(nested.read_text()) == ["111"]

    def test_state_file_sorted(self, state_file):
        d = Deduplicator(state_file)
        d.mark_seen([_listing("333"), _listing("111"), _listing("222")])
        d.save()
        data = json.loads(state_file.read_text())
        assert data == sorted(data)

    def test_missing_state_file_returns_empty(self, state_file):
        d = Deduplicator(state_file)
        assert d.filter_new([_listing("111")]) == [_listing("111")]

    def test_corrupt_state_file_is_ignored(self, state_file):
        state_file.write_text("not valid json{{{")
        d = Deduplicator(state_file)
        assert len(d.filter_new([_listing("111")])) == 1

    def test_wrong_type_in_state_file_is_ignored(self, state_file):
        state_file.write_text(json.dumps({"id": "111"}))
        d = Deduplicator(state_file)
        assert len(d.filter_new([_listing("111")])) == 1
