#!/usr/bin/python

# SPDX-FileCopyrightText: 2023-2026 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

import sqlite3
import urllib.parse

from rdflib_ocdm.counter_handler.counter_handler import CounterHandler


class SqliteCounterHandler(CounterHandler):
    """A concrete implementation of the ``CounterHandler`` interface
    that persistently stores the counter values within a SQLite
    database."""

    def __init__(self, database: str) -> None:
        """
        Constructor of the ``SqliteCounterHandler`` class.

        :param database: The name of the database
        :type info_dir: str
        """
        sqlite3.threadsafety = 3
        self.con = sqlite3.connect(database, check_same_thread=False)
        self.cur = self.con.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS info(
            entity TEXT PRIMARY KEY, 
            count INTEGER)""")

    def set_counter(self, new_value: int, entity_name: str) -> None:
        """
        It allows to set the counter value of provenance
        entities.

        :param new_value: The new counter value to be set
        :type new_value: int
        :param entity_name: The entity name
        :type entity_name: str
        :raises ValueError: if ``new_value`` is a negative integer.
        :return: None
        """
        entity_name = urllib.parse.quote(str(entity_name))
        if new_value < 0:
            raise ValueError("new_value must be a non negative integer!")
        self.cur.execute(
            "INSERT OR REPLACE INTO info (entity, count)"
            f" VALUES ('{entity_name}', {new_value})"
        )
        self.con.commit()

    def read_counter(self, entity_name: str) -> int:
        """
        It allows to read the counter value of provenance entities.

        :param entity_name: The entity name
        :type entity_name: str
        :return: The requested counter value.
        """
        entity_name = urllib.parse.quote(str(entity_name))
        result = self.cur.execute(
            f"SELECT count FROM info WHERE entity='{entity_name}'"
        )
        rows = result.fetchall()
        if len(rows) == 1:
            return rows[0][0]
        elif len(rows) == 0:
            return 0
        else:
            raise Exception(
                "There is more than one counter for this entity. The database is broken"
            )

    def increment_counter(self, entity_name: str) -> int:
        """
        It allows to increment the counter value of graph and
        provenance entities by one unit.

        :param entity_name: The entity name
        :type entity_name: str
        :return: The newly-updated (already incremented) counter value.
        """
        cur_count = self.read_counter(entity_name)
        count = cur_count + 1
        self.set_counter(count, entity_name)
        return count

    def close(self) -> None:
        """
        Closes the database connection.

        :return: None
        """
        try:
            if hasattr(self, "cur") and self.cur:
                self.cur.close()
        except (sqlite3.ProgrammingError, Exception):
            pass
        try:
            if hasattr(self, "con") and self.con:
                self.con.close()
        except (sqlite3.ProgrammingError, Exception):
            pass

    def __del__(self) -> None:
        """
        Destructor that ensures the database connection is closed.

        :return: None
        """
        self.close()

    def __enter__(self):
        """
        Context manager entry point.

        :return: self
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ARG002
        """
        Context manager exit point that ensures the database connection is closed.

        :param exc_type: Exception type
        :param exc_val: Exception value
        :param exc_tb: Exception traceback
        :return: None
        """
        self.close()
