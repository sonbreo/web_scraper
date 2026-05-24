import pytest
from unittest.mock import MagicMock, patch
from src.config import _validate
from src.runner import run


_VALID_CONFIG = {
    "searches": [{"url": "https://www.gumtree.com.au/s-ad/1", "keywords": []}],
    "filters": {
        "price": {"min": 0, "max": 999999},
        "max_age_days": None,
        "exclude_keywords": [],
        "seller_type": "all",
        "location": None,
    },
    "features": {
        "notifications": {"email": False, "discord": False},
        "output": {"csv": False, "json": False, "sqlite": False},
    },
    "http": {"request_delay": 0, "timeout": 10, "max_retries": 0, "proxies": []},
    "scheduling": {"interval_seconds": 900},
}


class TestConfigValidation:
    def test_valid_config_passes(self):
        _validate(_VALID_CONFIG)  # no exception

    def test_missing_searches_raises(self):
        cfg = {**_VALID_CONFIG, "searches": []}
        with pytest.raises(ValueError, match="searches"):
            _validate(cfg)

    def test_invalid_url_raises(self):
        cfg = {**_VALID_CONFIG, "searches": [{"url": "not-a-url"}]}
        with pytest.raises(ValueError, match="url"):
            _validate(cfg)

    def test_missing_url_raises(self):
        cfg = {**_VALID_CONFIG, "searches": [{"keywords": ["x"]}]}
        with pytest.raises(ValueError, match="url"):
            _validate(cfg)

    def test_negative_price_raises(self):
        import copy
        cfg = copy.deepcopy(_VALID_CONFIG)
        cfg["filters"]["price"]["min"] = -1
        with pytest.raises(ValueError, match="price"):
            _validate(cfg)

    def test_min_exceeds_max_raises(self):
        import copy
        cfg = copy.deepcopy(_VALID_CONFIG)
        cfg["filters"]["price"] = {"min": 500, "max": 100}
        with pytest.raises(ValueError, match="price"):
            _validate(cfg)

    def test_invalid_seller_type_raises(self):
        import copy
        cfg = copy.deepcopy(_VALID_CONFIG)
        cfg["filters"]["seller_type"] = "unknown_type"
        with pytest.raises(ValueError, match="seller_type"):
            _validate(cfg)

    def test_zero_max_age_days_raises(self):
        import copy
        cfg = copy.deepcopy(_VALID_CONFIG)
        cfg["filters"]["max_age_days"] = 0
        with pytest.raises(ValueError, match="max_age_days"):
            _validate(cfg)

    def test_negative_max_age_days_raises(self):
        import copy
        cfg = copy.deepcopy(_VALID_CONFIG)
        cfg["filters"]["max_age_days"] = -1
        with pytest.raises(ValueError, match="max_age_days"):
            _validate(cfg)

    def test_zero_timeout_raises(self):
        import copy
        cfg = copy.deepcopy(_VALID_CONFIG)
        cfg["http"]["timeout"] = 0
        with pytest.raises(ValueError, match="timeout"):
            _validate(cfg)

    def test_zero_interval_raises(self):
        import copy
        cfg = copy.deepcopy(_VALID_CONFIG)
        cfg["scheduling"]["interval_seconds"] = 0
        with pytest.raises(ValueError, match="interval"):
            _validate(cfg)


class TestRunnerRobustness:
    def test_failed_search_does_not_crash_run(self):
        import copy
        cfg = copy.deepcopy(_VALID_CONFIG)
        cfg["searches"] = [
            {"url": "https://www.gumtree.com.au/s-ad/1", "keywords": []},
            {"url": "https://www.gumtree.com.au/s-ad/2", "keywords": []},
        ]

        call_count = 0

        def fake_iter_pages(fetcher, url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("simulated network failure")
            return iter([])

        with patch("src.runner.iter_pages", side_effect=fake_iter_pages), \
             patch("src.runner.Deduplicator"), \
             patch("src.runner.Fetcher") as MockFetcher:
            MockFetcher.return_value.__enter__ = lambda s: MagicMock()
            MockFetcher.return_value.__exit__ = MagicMock(return_value=False)
            result = run(cfg, dry_run=True)

        # run completed despite the first search failing
        assert result == []
        assert call_count == 2
