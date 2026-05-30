# SPDX-FileCopyrightText: 2025-2026 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# SPDX-License-Identifier: ISC

import os
import sqlite3
import tempfile
import urllib.parse

import pytest

from rdflib_ocdm.counter_handler.filesystem_counter_handler import (
    FilesystemCounterHandler,
)
from rdflib_ocdm.counter_handler.in_memory_counter_handler import InMemoryCounterHandler
from rdflib_ocdm.counter_handler.sqlite_counter_handler import SqliteCounterHandler


class TestInMemoryCounterHandler:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.handler = InMemoryCounterHandler()

    def test_set_counter_valid_value(self):
        self.handler.set_counter(10, "test_entity")
        result = self.handler.read_counter("test_entity")
        assert result == 10

    def test_set_counter_negative_value(self):
        with pytest.raises(ValueError) as exc_info:
            self.handler.set_counter(-1, "test_entity")
        assert "non negative integer" in str(exc_info.value)

    def test_set_counter_zero_value(self):
        self.handler.set_counter(0, "test_entity")
        result = self.handler.read_counter("test_entity")
        assert result == 0

    def test_read_counter_nonexistent(self):
        result = self.handler.read_counter("nonexistent_entity")
        assert result == 0

    def test_increment_counter_new(self):
        result = self.handler.increment_counter("new_entity")
        assert result == 1

    def test_increment_counter_existing(self):
        self.handler.set_counter(5, "existing_entity")
        result = self.handler.increment_counter("existing_entity")
        assert result == 6


class TestFilesystemCounterHandler:
    def test_init_with_none_info_dir(self):
        with pytest.raises(ValueError) as exc_info:
            FilesystemCounterHandler(None)  # type: ignore[arg-type]
        assert "required" in str(exc_info.value)

    def test_init_with_empty_info_dir(self):
        with pytest.raises(ValueError) as exc_info:
            FilesystemCounterHandler("")
        assert "required" in str(exc_info.value)

    def test_init_with_info_dir_with_separator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            info_dir_with_sep = temp_dir + os.sep
            handler = FilesystemCounterHandler(info_dir_with_sep)
            assert handler.info_dir == info_dir_with_sep

    def test_set_counter_valid_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            handler.set_counter(10, "test_entity")
            result = handler.read_counter("test_entity")
            assert result == 10

    def test_set_counter_negative_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            with pytest.raises(ValueError) as exc_info:
                handler.set_counter(-1, "test_entity")
            assert "non negative integer" in str(exc_info.value)

    def test_read_counter_nonexistent_entity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            handler.set_counter(5, "entity1")
            result = handler.read_counter("nonexistent_entity")
            assert result == 0

    def test_file_creation_on_first_use(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            info_dir = os.path.join(temp_dir, "subdir", "counters")
            handler = FilesystemCounterHandler(info_dir)

            assert not os.path.exists(info_dir)

            handler.set_counter(1, "test_entity")

            assert os.path.exists(info_dir)
            prov_file = os.path.join(info_dir, "provenance_index.json")
            assert os.path.isfile(prov_file)

    def test_increment_counter_new(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            result = handler.increment_counter("new_entity")
            assert result == 1

    def test_increment_counter_existing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            handler.set_counter(5, "existing_entity")
            result = handler.increment_counter("existing_entity")
            assert result == 6


class TestSqliteCounterHandler:
    def test_set_counter_valid_value(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            handler.set_counter(10, "test_entity")
            result = handler.read_counter("test_entity")
            assert result == 10
            handler.close()
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_set_counter_negative_value(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            with pytest.raises(ValueError) as exc_info:
                handler.set_counter(-1, "test_entity")
            assert "non negative integer" in str(exc_info.value)
            handler.close()
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_read_counter_nonexistent_entity(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            handler.set_counter(5, "entity1")
            result = handler.read_counter("nonexistent_entity")
            assert result == 0
            handler.close()
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_read_counter_database_corruption(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            handler.set_counter(5, "test_entity")

            con = sqlite3.connect(temp_db_path)
            cur = con.cursor()
            cur.execute("DROP TABLE info")
            cur.execute("""CREATE TABLE info(entity TEXT, count INTEGER)""")

            entity_encoded = urllib.parse.quote("test_entity")
            cur.execute(
                f"INSERT INTO info (entity, count) VALUES ('{entity_encoded}', 5)"
            )
            cur.execute(
                f"INSERT INTO info (entity, count) VALUES ('{entity_encoded}', 10)"
            )
            con.commit()
            con.close()

            with pytest.raises(Exception) as exc_info:
                handler.read_counter("test_entity")
            assert "more than one counter" in str(exc_info.value)
            handler.close()
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_increment_counter_new(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            result = handler.increment_counter("new_entity")
            assert result == 1
            handler.close()
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_increment_counter_existing(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            handler.set_counter(5, "existing_entity")
            result = handler.increment_counter("existing_entity")
            assert result == 6
            handler.close()
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
