import csv
import json
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch
from src.storage import save, _save_csv, _save_json, _save_sqlite
from src.parser import Listing


def _listing(listing_id="1234567890", price=300):
    return Listing(
        listing_id=listing_id,
        title="Nintendo Switch Console",
        price=price,
        price_raw=f"${price}",
        url=f"https://www.gumtree.com.au/s-ad/{listing_id}",
        location="Melbourne, VIC",
        date_raw="2 days ago",
        thumbnail_url=None,
        seller_type="private",
    )


def _cfg(**output_flags):
    flags = {"csv": False, "json": False, "sqlite": False}
    flags.update(output_flags)
    return {"features": {"output": flags}}


@pytest.fixture(autouse=True)
def patch_output_dir(tmp_path):
    with patch("src.storage._OUTPUT_DIR", tmp_path):
        yield tmp_path


class TestSaveDispatch:
    def test_no_output_when_empty_listings(self, patch_output_dir):
        save([], _cfg(csv=True, json=True, sqlite=True))
        assert list(patch_output_dir.iterdir()) == []

    def test_csv_only(self, patch_output_dir):
        save([_listing()], _cfg(csv=True))
        assert (patch_output_dir / "listings.csv").exists()
        assert not (patch_output_dir / "listings.json").exists()

    def test_json_only(self, patch_output_dir):
        save([_listing()], _cfg(json=True))
        assert (patch_output_dir / "listings.json").exists()
        assert not (patch_output_dir / "listings.csv").exists()

    def test_sqlite_only(self, patch_output_dir):
        save([_listing()], _cfg(sqlite=True))
        assert (patch_output_dir / "listings.db").exists()


class TestCSV:
    def test_header_and_row(self, patch_output_dir):
        _save_csv([_listing()])
        path = patch_output_dir / "listings.csv"
        rows = list(csv.DictReader(path.open()))
        assert len(rows) == 1
        assert rows[0]["listing_id"] == "1234567890"
        assert rows[0]["title"] == "Nintendo Switch Console"

    def test_appends_on_second_call(self, patch_output_dir):
        _save_csv([_listing("111")])
        _save_csv([_listing("222")])
        rows = list(csv.DictReader((patch_output_dir / "listings.csv").open()))
        assert len(rows) == 2

    def test_header_written_once(self, patch_output_dir):
        _save_csv([_listing("111")])
        _save_csv([_listing("222")])
        lines = (patch_output_dir / "listings.csv").read_text().splitlines()
        headers = [l for l in lines if l.startswith("listing_id")]
        assert len(headers) == 1


class TestJSON:
    def test_creates_valid_json(self, patch_output_dir):
        _save_json([_listing()])
        data = json.loads((patch_output_dir / "listings.json").read_text())
        assert isinstance(data, list)
        assert data[0]["listing_id"] == "1234567890"

    def test_appends_to_existing(self, patch_output_dir):
        _save_json([_listing("111")])
        _save_json([_listing("222")])
        data = json.loads((patch_output_dir / "listings.json").read_text())
        assert len(data) == 2

    def test_corrupt_existing_json_is_overwritten(self, patch_output_dir):
        (patch_output_dir / "listings.json").write_text("not json{{{")
        _save_json([_listing()])
        data = json.loads((patch_output_dir / "listings.json").read_text())
        assert len(data) == 1


class TestSQLite:
    def test_table_created_and_row_inserted(self, patch_output_dir):
        _save_sqlite([_listing()])
        with sqlite3.connect(patch_output_dir / "listings.db") as conn:
            rows = conn.execute("SELECT listing_id, title FROM listings").fetchall()
        assert rows == [("1234567890", "Nintendo Switch Console")]

    def test_duplicate_id_not_inserted_twice(self, patch_output_dir):
        _save_sqlite([_listing()])
        _save_sqlite([_listing()])
        with sqlite3.connect(patch_output_dir / "listings.db") as conn:
            count = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
        assert count == 1

    def test_multiple_listings(self, patch_output_dir):
        _save_sqlite([_listing("111"), _listing("222")])
        with sqlite3.connect(patch_output_dir / "listings.db") as conn:
            count = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
        assert count == 2
