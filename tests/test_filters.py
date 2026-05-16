import pytest
from src.filters import apply_filters, _parse_age_days
from src.parser import Listing


def _listing(**kwargs) -> Listing:
    defaults = dict(
        listing_id="1234567890",
        title="Nintendo Switch Console",
        price=300,
        price_raw="$300",
        url="https://www.gumtree.com.au/s-ad/1234567890",
        location="Melbourne, VIC",
        date_raw="2 days ago",
        thumbnail_url=None,
        seller_type="private",
    )
    defaults.update(kwargs)
    return Listing(**defaults)


_BASE_FILTERS: dict = {
    "price": {"min": 0, "max": 999999},
    "max_age_days": None,
    "exclude_keywords": [],
    "seller_type": "all",
    "location": None,
}


def _filters(**kwargs) -> dict:
    import copy
    f = copy.deepcopy(_BASE_FILTERS)
    f.update(kwargs)
    return f


class TestKeywordFilter:
    def test_all_keywords_present(self):
        result = apply_filters([_listing()], _filters(), keywords=["nintendo", "switch"])
        assert len(result) == 1

    def test_missing_keyword_drops_listing(self):
        result = apply_filters([_listing()], _filters(), keywords=["xbox"])
        assert result == []

    def test_case_insensitive(self):
        result = apply_filters([_listing()], _filters(), keywords=["NINTENDO", "SWITCH"])
        assert len(result) == 1

    def test_no_keywords_keeps_all(self):
        listings = [_listing(), _listing(title="Something else")]
        result = apply_filters(listings, _filters(), keywords=None)
        assert len(result) == 2


class TestPriceFilter:
    def test_within_range(self):
        result = apply_filters([_listing(price=300)], _filters(price={"min": 100, "max": 500}))
        assert len(result) == 1

    def test_below_min_dropped(self):
        result = apply_filters([_listing(price=50)], _filters(price={"min": 100, "max": 500}))
        assert result == []

    def test_above_max_dropped(self):
        result = apply_filters([_listing(price=600)], _filters(price={"min": 100, "max": 500}))
        assert result == []

    def test_none_price_not_dropped_by_range(self):
        # Listings with no parseable price pass price filter
        result = apply_filters([_listing(price=None)], _filters(price={"min": 100, "max": 500}))
        assert len(result) == 1

    def test_at_boundary_kept(self):
        result = apply_filters([_listing(price=100)], _filters(price={"min": 100, "max": 500}))
        assert len(result) == 1
        result = apply_filters([_listing(price=500)], _filters(price={"min": 100, "max": 500}))
        assert len(result) == 1


class TestExcludeKeywords:
    def test_excluded_keyword_drops_listing(self):
        result = apply_filters(
            [_listing(title="Nintendo Switch - parts only")],
            _filters(exclude_keywords=["parts only"]),
        )
        assert result == []

    def test_no_excluded_keyword_keeps_listing(self):
        result = apply_filters(
            [_listing(title="Nintendo Switch Console")],
            _filters(exclude_keywords=["broken", "faulty"]),
        )
        assert len(result) == 1

    def test_case_insensitive_exclude(self):
        result = apply_filters(
            [_listing(title="Nintendo Switch - BROKEN screen")],
            _filters(exclude_keywords=["broken"]),
        )
        assert result == []


class TestSellerTypeFilter:
    def test_private_only_keeps_private(self):
        result = apply_filters([_listing(seller_type="private")], _filters(seller_type="private"))
        assert len(result) == 1

    def test_private_only_drops_dealer(self):
        result = apply_filters([_listing(seller_type="dealer")], _filters(seller_type="private"))
        assert result == []

    def test_all_keeps_both(self):
        listings = [_listing(seller_type="private"), _listing(seller_type="dealer")]
        result = apply_filters(listings, _filters(seller_type="all"))
        assert len(result) == 2

    def test_unknown_seller_not_dropped_by_type_filter(self):
        result = apply_filters([_listing(seller_type="unknown")], _filters(seller_type="private"))
        assert len(result) == 1


class TestDateFilter:
    def test_within_age_kept(self):
        result = apply_filters([_listing(date_raw="2 days ago")], _filters(max_age_days=7))
        assert len(result) == 1

    def test_too_old_dropped(self):
        result = apply_filters([_listing(date_raw="10 days ago")], _filters(max_age_days=7))
        assert result == []

    def test_hours_within_range(self):
        result = apply_filters([_listing(date_raw="3 hours ago")], _filters(max_age_days=1))
        assert len(result) == 1

    def test_weeks_converted_correctly(self):
        result = apply_filters([_listing(date_raw="2 weeks ago")], _filters(max_age_days=7))
        assert result == []

    def test_no_max_age_keeps_all(self):
        result = apply_filters([_listing(date_raw="100 days ago")], _filters(max_age_days=None))
        assert len(result) == 1

    def test_unparseable_date_not_dropped(self):
        result = apply_filters([_listing(date_raw="yesterday")], _filters(max_age_days=1))
        assert len(result) == 1


class TestLocationFilter:
    def test_matching_location_kept(self):
        result = apply_filters([_listing(location="Melbourne, VIC")], _filters(location="Melbourne"))
        assert len(result) == 1

    def test_non_matching_location_dropped(self):
        result = apply_filters([_listing(location="Sydney, NSW")], _filters(location="Melbourne"))
        assert result == []

    def test_case_insensitive_location(self):
        result = apply_filters([_listing(location="Melbourne, VIC")], _filters(location="melbourne"))
        assert len(result) == 1

    def test_no_location_filter_keeps_all(self):
        result = apply_filters([_listing(location="Sydney, NSW")], _filters(location=None))
        assert len(result) == 1

    def test_none_listing_location_not_dropped(self):
        result = apply_filters([_listing(location=None)], _filters(location="Melbourne"))
        assert len(result) == 1


class TestParseAgeDays:
    @pytest.mark.parametrize("raw,expected", [
        ("3 days ago", 3.0),
        ("2 weeks ago", 14.0),
        ("1 hour ago", 1 / 24),
        ("30 minutes ago", 30 / 1440),
        ("1 month ago", 30.0),
        ("1 year ago", 365.0),
    ])
    def test_parse(self, raw, expected):
        assert _parse_age_days(raw) == pytest.approx(expected)

    def test_unparseable_returns_none(self):
        assert _parse_age_days("yesterday") is None
        assert _parse_age_days("") is None
