import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.cli import _apply_overrides, _configure_logging, main
import logging
import argparse


_BASE_CONFIG = {
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
        "output": {"csv": True, "json": False, "sqlite": False},
    },
    "http": {"request_delay": 0, "timeout": 10, "max_retries": 0, "proxies": []},
    "scheduling": {"interval_seconds": 900},
}


def _args(**kwargs):
    defaults = dict(
        min_price=None, max_price=None, location=None, seller_type=None,
        csv=None, json=None, sqlite=None,
        verbose=False, quiet=False, dry_run=False, once=True, interval=None,
        config=Path("config/settings.yaml"),
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


import copy


class TestApplyOverrides:
    def test_min_price_override(self):
        cfg = copy.deepcopy(_BASE_CONFIG)
        result = _apply_overrides(cfg, _args(min_price=200))
        assert result["filters"]["price"]["min"] == 200

    def test_max_price_override(self):
        cfg = copy.deepcopy(_BASE_CONFIG)
        result = _apply_overrides(cfg, _args(max_price=400))
        assert result["filters"]["price"]["max"] == 400

    def test_location_override(self):
        cfg = copy.deepcopy(_BASE_CONFIG)
        result = _apply_overrides(cfg, _args(location="Sydney"))
        assert result["filters"]["location"] == "Sydney"

    def test_seller_type_override(self):
        cfg = copy.deepcopy(_BASE_CONFIG)
        result = _apply_overrides(cfg, _args(seller_type="private"))
        assert result["filters"]["seller_type"] == "private"

    def test_csv_flag_enables_csv(self):
        cfg = copy.deepcopy(_BASE_CONFIG)
        cfg["features"]["output"]["csv"] = False
        result = _apply_overrides(cfg, _args(csv=True))
        assert result["features"]["output"]["csv"] is True

    def test_json_flag_enables_json(self):
        cfg = copy.deepcopy(_BASE_CONFIG)
        result = _apply_overrides(cfg, _args(json=True))
        assert result["features"]["output"]["json"] is True

    def test_sqlite_flag_enables_sqlite(self):
        cfg = copy.deepcopy(_BASE_CONFIG)
        result = _apply_overrides(cfg, _args(sqlite=True))
        assert result["features"]["output"]["sqlite"] is True

    def test_none_overrides_are_ignored(self):
        cfg = copy.deepcopy(_BASE_CONFIG)
        original_min = cfg["filters"]["price"]["min"]
        result = _apply_overrides(cfg, _args())
        assert result["filters"]["price"]["min"] == original_min


class TestConfigureLogging:
    def test_verbose_sets_debug(self):
        _configure_logging(verbose=True, quiet=False)
        assert logging.getLogger().level == logging.DEBUG

    def test_quiet_sets_warning(self):
        _configure_logging(verbose=False, quiet=True)
        assert logging.getLogger().level == logging.WARNING

    def test_default_sets_info(self):
        _configure_logging(verbose=False, quiet=False)
        assert logging.getLogger().level == logging.INFO


class TestMainEntryPoint:
    def test_once_calls_run_once(self, tmp_path):
        config_file = tmp_path / "settings.yaml"
        config_file.write_text(
            "searches:\n  - url: https://example.com\n    keywords: []\n"
        )
        with patch("src.cli.load_config", return_value=copy.deepcopy(_BASE_CONFIG)), \
             patch("src.cli.run_once") as mock_once, \
             patch("sys.argv", ["gumtree-scraper", "--once"]):
            main()
        mock_once.assert_called_once()

    def test_bad_config_exits_with_error(self, tmp_path):
        with patch("src.cli.load_config", side_effect=ValueError("bad config")), \
             patch("sys.argv", ["gumtree-scraper", "--once"]):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code == 1

    def test_interval_calls_run_loop(self):
        with patch("src.cli.load_config", return_value=copy.deepcopy(_BASE_CONFIG)), \
             patch("src.cli.run_loop") as mock_loop, \
             patch("sys.argv", ["gumtree-scraper", "--interval", "30"]):
            main()
        mock_loop.assert_called_once()
        _, kwargs = mock_loop.call_args
        assert mock_loop.call_args[1].get("interval_seconds") == 30 or \
               mock_loop.call_args[0][1] == 30
