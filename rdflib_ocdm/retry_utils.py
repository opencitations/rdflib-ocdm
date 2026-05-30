#!/usr/bin/python

# SPDX-FileCopyrightText: 2023-2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def execute_with_retry(
    func: Callable[..., T],
    *args: object,
    max_retries: int = 5,
    base_wait_time: float = 1,
    reporter: object | None = None,
    **kwargs: object,
) -> T:
    """
    A function that executes the given function with retry logic
    and exponential backoff. This is useful when you can't use the
    decorator directly.

    :param func: The function to execute with retry logic
    :param args: Positional arguments to pass to the function
    :param max_retries: Maximum number of retry attempts before
      giving up
    :param base_wait_time: Initial wait time in seconds, which will
      be increased exponentially
    :param reporter: Optional reporter object with add_sentence
      method for logging
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
                wait_time = (base_wait_time * (2 ** (retry_count - 1))) + (
                    random.random() * 0.5
                )

                # Log the retry attempt
                message = (
                    f"Query attempt {retry_count}/{max_retries}"
                    f" failed: {e}."
                    f" Retrying in {wait_time:.2f} seconds..."
                )
                if reporter is not None and hasattr(reporter, "add_sentence"):
                    reporter.add_sentence(message)  # type: ignore[attr-defined]
                else:
                    print(message)

                time.sleep(wait_time)
            else:
                error_message = f"Failed after {max_retries} attempts: {e}"
                if reporter is not None and hasattr(reporter, "add_sentence"):
                    reporter.add_sentence(f"[ERROR] {error_message}")  # type: ignore[attr-defined]
                raise ValueError(error_message)
    raise ValueError(f"Failed after {max_retries} attempts")
