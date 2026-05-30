#!/usr/bin/python

# SPDX-FileCopyrightText: 2016 Silvio Peroni <essepuntato@gmail.com>
# SPDX-FileCopyrightText: 2023-2026 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from rdflib_ocdm.counter_handler.counter_handler import CounterHandler


class InMemoryCounterHandler(CounterHandler):
    """A concrete implementation of the ``CounterHandler`` interface
    that temporarily stores the counter values in the volatile system
    memory."""

    def __init__(self) -> None:
        """
        Constructor of the ``InMemoryCounterHandler`` class.
        """
        self.prov_counters = dict()

    def set_counter(self, new_value: int, entity_name: str) -> None:
        """
        It allows to set the counter value of graph and provenance entities.

        :param new_value: The new counter value to be set
        :type new_value: int
        :param entity_name: The entity name
        :type entity_name: str
        :raises ValueError: if ``new_value`` is a negative integer.
        :return: None
        """
        entity_name = str(entity_name)
        if new_value < 0:
            raise ValueError("new_value must be a non negative integer!")
        self.prov_counters[entity_name] = new_value

    def read_counter(self, entity_name: str) -> int:
        """
        It allows to read the counter value of provenance entities.

        :param entity_name: The entity name
        :type entity_name: str
        :return: The requested counter value.
        """
        entity_name = str(entity_name)
        if entity_name in self.prov_counters:
            return self.prov_counters[entity_name]
        else:
            self.prov_counters[entity_name] = 0
            return 0

    def increment_counter(self, entity_name: str) -> int:
        """
        It allows to increment the counter value of graph and
        provenance entities by one unit.

        :param entity_name: The entity name
        :type entity_name: str
        :return: The newly-updated (already incremented) counter value.
        """
        entity_name = str(entity_name)
        if entity_name in self.prov_counters:
            self.prov_counters[entity_name] += 1
        else:
            self.prov_counters[entity_name] = 1
        return self.prov_counters[entity_name]
