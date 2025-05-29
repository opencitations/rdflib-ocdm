#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2023, Arcangelo Massari <arcangelo.massari@unibo.it>
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

import redis


class RedisCounterHandler:
    def __init__(self, host, port, db: int, password=None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.connection = None

    def connect(self):
        self.connection = redis.Redis(host=self.host, port=self.port, db=self.db, password=self.password)

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def set_counter(self, new_value: int, entity_name: str) -> None:
        entity_name = str(entity_name)
        if new_value < 0:
            raise ValueError("new_value must be a non negative integer!")
        self.connection.set(entity_name, new_value)

    def read_counter(self, entity_name: str) -> int:
        entity_name = str(entity_name)
        result = self.connection.get(entity_name)
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
    
    def flush(self):
        self.connection.flushdb()
