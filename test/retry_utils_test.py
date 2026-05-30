# SPDX-FileCopyrightText: 2025-2026 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from unittest.mock import MagicMock, patch

import pytest

from rdflib_ocdm.retry_utils import execute_with_retry


class MockReporter:
    def __init__(self):
        self.messages = []

    def add_sentence(self, message):
        self.messages.append(message)


class TestRetryUtils:
    def test_execute_with_retry_success_first_attempt(self):
        mock_func = MagicMock(return_value="success")
        result = execute_with_retry(
            mock_func, "arg1", "arg2", kwarg1="kwarg1", kwarg2="kwarg2"
        )

        assert result == "success"
        mock_func.assert_called_once_with(
            "arg1", "arg2", kwarg1="kwarg1", kwarg2="kwarg2"
        )

    def test_execute_with_retry_success_after_retries(self):
        mock_func = MagicMock(
            side_effect=[Exception("Error 1"), Exception("Error 2"), "success"]
        )

        with patch("time.sleep"):
            result = execute_with_retry(mock_func, max_retries=3, base_wait_time=0.1)

        assert result == "success"
        assert mock_func.call_count == 3
        # mock_sleep not needed for assertion here since we're testing the func

    def test_execute_with_retry_with_reporter(self):
        mock_reporter = MockReporter()
        mock_func = MagicMock(side_effect=[Exception("Test error"), "success"])

        with patch("time.sleep"):
            result = execute_with_retry(
                mock_func, reporter=mock_reporter, max_retries=2, base_wait_time=0.1
            )

        assert result == "success"
        assert mock_func.call_count == 2
        assert len(mock_reporter.messages) == 1
        assert "Test error" in mock_reporter.messages[0]

    def test_execute_with_retry_all_attempts_fail(self):
        mock_reporter = MockReporter()
        mock_func = MagicMock(side_effect=Exception("Persistent error"))

        with patch("time.sleep"):
            with pytest.raises(ValueError) as exc_info:
                execute_with_retry(mock_func, max_retries=3, reporter=mock_reporter)

        assert "Failed after 3 attempts" in str(exc_info.value)
        assert mock_func.call_count == 4
        assert len(mock_reporter.messages) == 4
        assert "[ERROR]" in mock_reporter.messages[-1]
