# SPDX-FileCopyrightText: 2025 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

from unittest.mock import patch

import pytest

from rdflib_ocdm.counter_handler.redis_counter_handler import RedisCounterHandler


class TestRedisCounterHandler:
    @pytest.fixture(autouse=True)
    def setup(self, fake_redis):
        fake_redis.flushall()
        self.fake_redis = fake_redis
        with patch("redis.Redis", return_value=fake_redis):
            self.handler = RedisCounterHandler(host="localhost", port=6379, db=0)
            self.handler.connect()
            yield
            self.handler.disconnect()

    def test_set_counter_valid_value(self):
        self.handler.set_counter(10, "test_entity")
        result = self.fake_redis.get("test_entity")
        assert int(result) == 10  # type: ignore[arg-type]

    def test_set_counter_negative_value(self):
        with pytest.raises(ValueError):
            self.handler.set_counter(-1, "test_entity")

    def test_read_counter_existing(self):
        self.fake_redis.set("test_entity", 5)
        result = self.handler.read_counter("test_entity")
        assert result == 5

    def test_read_counter_nonexistent(self):
        result = self.handler.read_counter("nonexistent_entity")
        assert result == 0

    def test_increment_counter_new(self):
        result = self.handler.increment_counter("new_entity")
        assert result == 1
        assert int(self.fake_redis.get("new_entity")) == 1  # type: ignore[arg-type]

    def test_increment_counter_existing(self):
        self.fake_redis.set("existing_entity", 5)
        result = self.handler.increment_counter("existing_entity")
        assert result == 6
        assert int(self.fake_redis.get("existing_entity")) == 6  # type: ignore[arg-type]

    def test_flush(self):
        self.fake_redis.set("entity1", 1)
        self.fake_redis.set("entity2", 2)
        self.handler.flush()
        assert self.fake_redis.get("entity1") is None
        assert self.fake_redis.get("entity2") is None

    def test_disconnect_no_connection(self):
        handler = RedisCounterHandler(host="localhost", port=6379, db=0)
        handler.disconnect()
        handler.disconnect()
