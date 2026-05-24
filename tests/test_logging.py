import logging
import pytest
from pathlib import Path
from unittest.mock import patch
from src.cli import _configure_logging


@pytest.fixture(autouse=True)
def reset_root_logger():
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    yield
    root.handlers = original_handlers
    root.setLevel(original_level)


class TestLogLevels:
    def test_verbose_sets_debug(self):
        _configure_logging(verbose=True, quiet=False)
        assert logging.getLogger().level == logging.DEBUG

    def test_quiet_sets_warning(self):
        _configure_logging(verbose=False, quiet=True)
        assert logging.getLogger().level == logging.WARNING

    def test_default_sets_info(self):
        _configure_logging(verbose=False, quiet=False)
        assert logging.getLogger().level == logging.INFO


class TestFileLogging:
    def test_log_file_is_created(self, tmp_path):
        log_path = tmp_path / "test.log"
        _configure_logging(verbose=False, quiet=False, log_file=str(log_path))
        logging.getLogger("test.file").info("hello file")
        assert log_path.exists()
        assert "hello file" in log_path.read_text()

    def test_file_handler_is_added(self, tmp_path):
        log_path = tmp_path / "scraper.log"
        _configure_logging(verbose=False, quiet=False, log_file=str(log_path))
        handlers = logging.getLogger().handlers
        file_handlers = [h for h in handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1

    def test_log_file_parent_created(self, tmp_path):
        log_path = tmp_path / "nested" / "dir" / "app.log"
        _configure_logging(verbose=False, quiet=False, log_file=str(log_path))
        assert log_path.parent.exists()

    def test_log_file_contains_formatted_output(self, tmp_path):
        log_path = tmp_path / "fmt.log"
        _configure_logging(verbose=False, quiet=False, log_file=str(log_path))
        logging.getLogger("src.test_module").warning("something went wrong")
        content = log_path.read_text()
        assert "WARNING" in content
        assert "src.test_module" in content
        assert "something went wrong" in content
