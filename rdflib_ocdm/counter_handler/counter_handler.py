#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2016, Silvio Peroni <essepuntato@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.
from abc import ABC, abstractmethod


class CounterHandler(ABC):
    """Abstract class representing the interface for every concrete counter handler."""

    @abstractmethod
    def set_counter(self, new_value: int, entity_name: str) -> None:
        """
        Method signature for concrete implementations that allow setting the counter value
        of provenance entities.

        :param new_value: The new counter value to be set
        :type new_value: int
        :param entity_name: The entity name
        :type entity_name: str
        :raises NotImplementedError: always
        :return: None
        """
        raise NotImplementedError

    @abstractmethod
    def read_counter(self, entity_name: str) -> int:
        """
        Method signature for concrete implementations that allow reading the counter value
        of graph and provenance entities.

        :param entity_name: The entity name
        :type entity_name: str
        :raises NotImplementedError: always
        :return: The requested counter value.
        """
        raise NotImplementedError

    @abstractmethod
    def increment_counter(self, entity_name: str) -> int:
        """
        Method signature for concrete implementations that allow incrementing by one unit
        the counter value of graph and provenance entities.

        :param entity_name: The entity name
        :type entity_name: str
        :raises NotImplementedError: always
        :return: The newly-updated (already incremented) counter value.
        """
        raise NotImplementedError