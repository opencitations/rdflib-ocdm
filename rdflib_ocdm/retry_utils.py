#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Arcangelo Massari <arcangelo.massari@unibo.it>
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

from __future__ import annotations

import random
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

T = TypeVar('T')


def execute_with_retry(func: Callable[..., T], *args: Any, max_retries: int = 5, 
                      base_wait_time: int = 1, reporter: Any = None, **kwargs: Any) -> T:
    """
    A function that executes the given function with retry logic and exponential backoff.
    This is useful when you can't use the decorator directly.
    
    :param func: The function to execute with retry logic
    :param args: Positional arguments to pass to the function
    :param max_retries: Maximum number of retry attempts before giving up
    :param base_wait_time: Initial wait time in seconds, which will be increased exponentially
    :param reporter: Optional reporter object with add_sentence method for logging
    :param kwargs: Keyword arguments to pass to the function
    :return: The result of the function call
    """
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                # Calculate wait time with exponential backoff and some randomness
                wait_time = (base_wait_time * (2 ** (retry_count - 1))) + (random.random() * 0.5)
                
                # Log the retry attempt
                message = f"Query attempt {retry_count}/{max_retries} failed: {e}. Retrying in {wait_time:.2f} seconds..."
                if reporter and hasattr(reporter, 'add_sentence'):
                    reporter.add_sentence(message)
                else:
                    print(message)
                    
                time.sleep(wait_time)
            else:
                # All retries failed
                error_message = f"Failed after {max_retries} attempts: {e}"
                if reporter and hasattr(reporter, 'add_sentence'):
                    reporter.add_sentence(f"[ERROR] {error_message}")
                raise ValueError(error_message)