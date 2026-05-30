#!/usr/bin/python

# SPDX-FileCopyrightText: 2023-2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from __future__ import annotations

import redis


class RedisCounterHandler:
    def __init__(self, host: str, port: int, db: int, password: str | None = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.connection: redis.Redis | None = None  # type: ignore[type-arg]

    def connect(self) -> None:
        self.connection = redis.Redis(host=self.host, port=self.port, db=self.db, password=self.password)

    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()

    def set_counter(self, new_value: int, entity_name: str) -> None:
        entity_name = str(entity_name)
        if new_value < 0:
            raise ValueError("new_value must be a non negative integer!")
        assert self.connection is not None
        self.connection.set(entity_name, new_value)

    def read_counter(self, entity_name: str) -> int:
        entity_name = str(entity_name)
        assert self.connection is not None
        result: bytes | None = self.connection.get(entity_name)  # type: ignore[assignment]
        if result:
            return int(result.decode('utf-8'))
        else:
            return 0

    def increment_counter(self, entity_name: str) -> int:
        entity_name = str(entity_name)
        cur_count = self.read_counter(entity_name)
        count = cur_count + 1
        self.set_counter(count, entity_name)
        return count

    def flush(self) -> None:
        assert self.connection is not None
        self.connection.flushdb()
