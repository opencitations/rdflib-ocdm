#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

import unittest
from unittest.mock import MagicMock, patch

from rdflib_ocdm.retry_utils import execute_with_retry


class MockReporter:
    def __init__(self):
        self.messages = []
    
    def add_sentence(self, message):
        self.messages.append(message)

class TestRetryUtils(unittest.TestCase):
    
    def test_execute_with_retry_success_first_attempt(self):
        # Test successful execution on first attempt
        mock_func = MagicMock(return_value="success")
        result = execute_with_retry(mock_func, "arg1", "arg2", kwarg1="kwarg1", kwarg2="kwarg2")
        
        self.assertEqual(result, "success")
        mock_func.assert_called_once_with("arg1", "arg2", kwarg1="kwarg1", kwarg2="kwarg2")
    
    def test_execute_with_retry_success_after_retries(self):
        # Test successful execution after a few retries
        mock_func = MagicMock(side_effect=[Exception("Error 1"), Exception("Error 2"), "success"])
        
        with patch('time.sleep') as mock_sleep:  # Mock sleep to speed up test
            result = execute_with_retry(mock_func, max_retries=3, base_wait_time=0.1)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Should sleep twice (after first and second failures)
    
    def test_execute_with_retry_with_reporter(self):
        # Test with a reporter object
        mock_reporter = MockReporter()
        mock_func = MagicMock(side_effect=[Exception("Test error"), "success"])
        
        with patch('time.sleep') as mock_sleep:
            result = execute_with_retry(mock_func, reporter=mock_reporter, max_retries=2, base_wait_time=0.1)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
        self.assertEqual(len(mock_reporter.messages), 1)  # Should have one message about retry
        self.assertTrue("Test error" in mock_reporter.messages[0])
    
    def test_execute_with_retry_all_attempts_fail(self):
        # Test when all retry attempts fail
        mock_reporter = MockReporter()
        mock_func = MagicMock(side_effect=Exception("Persistent error"))
        
        with patch('time.sleep'), self.assertRaises(ValueError) as context:
            execute_with_retry(mock_func, max_retries=3, reporter=mock_reporter)
        
        self.assertTrue("Failed after 3 attempts" in str(context.exception))
        self.assertEqual(mock_func.call_count, 4)  # Initial + 3 retries
        self.assertEqual(len(mock_reporter.messages), 4)  # 3 retry messages + 1 error message
        self.assertTrue("[ERROR]" in mock_reporter.messages[-1])

if __name__ == '__main__':
    unittest.main()
