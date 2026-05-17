import pytest
from unittest.mock import MagicMock, patch, call
from src.scheduler import run_once, run_loop


class TestRunOnce:
    def test_calls_job_once(self):
        job = MagicMock()
        run_once(job)
        job.assert_called_once()

    def test_propagates_exception(self):
        job = MagicMock(side_effect=RuntimeError("boom"))
        with pytest.raises(RuntimeError, match="boom"):
            run_once(job)


class TestRunLoop:
    def test_calls_job_multiple_times(self):
        job = MagicMock()
        call_count = 0

        def counting_job():
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                raise KeyboardInterrupt

        with patch("src.scheduler.time.sleep"):
            with pytest.raises(KeyboardInterrupt):
                run_loop(counting_job, interval_seconds=1)

        assert call_count == 3

    def test_sleep_called_between_runs(self):
        call_count = 0

        def job():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise KeyboardInterrupt

        with patch("src.scheduler.time.sleep") as mock_sleep, \
             patch("src.scheduler.time.monotonic", return_value=0.0):
            with pytest.raises(KeyboardInterrupt):
                run_loop(job, interval_seconds=60)

        mock_sleep.assert_called()

    def test_job_exception_does_not_stop_loop(self):
        call_count = 0

        def flaky_job():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("transient error")
            if call_count >= 2:
                raise KeyboardInterrupt

        with patch("src.scheduler.time.sleep"):
            with pytest.raises(KeyboardInterrupt):
                run_loop(flaky_job, interval_seconds=1)

        assert call_count == 2
