#!/usr/bin/python

# SPDX-FileCopyrightText: 2016 Silvio Peroni <essepuntato@gmail.com>
# SPDX-FileCopyrightText: 2023-2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC
from abc import ABC, abstractmethod


class CounterHandler(ABC):  # pragma: no cover
    """Abstract class representing the interface for every concrete counter handler."""

    @abstractmethod
    def set_counter(self, new_value: int, entity_name: str) -> None:
        """
        Method signature for concrete implementations that allow
        setting the counter value of provenance entities.

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
        Method signature for concrete implementations that allow
        reading the counter value of graph and provenance entities.

        :param entity_name: The entity name
        :type entity_name: str
        :raises NotImplementedError: always
        :return: The requested counter value.
        """
        raise NotImplementedError

    @abstractmethod
    def increment_counter(self, entity_name: str) -> int:
        """
        Method signature for concrete implementations that allow
        incrementing by one unit the counter value of graph and
        provenance entities.

        :param entity_name: The entity name
        :type entity_name: str
        :raises NotImplementedError: always
        :return: The newly-updated (already incremented) counter value.
        """
        raise NotImplementedError


class SupplierAwareCounterHandler(CounterHandler, ABC):
    supplier_prefix: str
