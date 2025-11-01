#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sqlite3
import tempfile
import unittest

from rdflib_ocdm.counter_handler.filesystem_counter_handler import \
    FilesystemCounterHandler
from rdflib_ocdm.counter_handler.in_memory_counter_handler import \
    InMemoryCounterHandler
from rdflib_ocdm.counter_handler.sqlite_counter_handler import \
    SqliteCounterHandler


class TestInMemoryCounterHandler(unittest.TestCase):
    """Test InMemoryCounterHandler edge cases"""

    def setUp(self):
        self.handler = InMemoryCounterHandler()

    def test_set_counter_valid_value(self):
        """Test setting a valid counter value"""
        self.handler.set_counter(10, 'test_entity')
        result = self.handler.read_counter('test_entity')
        self.assertEqual(result, 10)

    def test_set_counter_negative_value(self):
        """Test that setting a negative value raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.handler.set_counter(-1, 'test_entity')
        self.assertIn("non negative integer", str(context.exception))

    def test_set_counter_zero_value(self):
        """Test setting counter to zero"""
        self.handler.set_counter(0, 'test_entity')
        result = self.handler.read_counter('test_entity')
        self.assertEqual(result, 0)

    def test_read_counter_nonexistent(self):
        """Test reading a non-existent counter returns 0"""
        result = self.handler.read_counter('nonexistent_entity')
        self.assertEqual(result, 0)

    def test_increment_counter_new(self):
        """Test incrementing a new counter starts at 1"""
        result = self.handler.increment_counter('new_entity')
        self.assertEqual(result, 1)

    def test_increment_counter_existing(self):
        """Test incrementing an existing counter"""
        self.handler.set_counter(5, 'existing_entity')
        result = self.handler.increment_counter('existing_entity')
        self.assertEqual(result, 6)


class TestFilesystemCounterHandler(unittest.TestCase):
    """Test FilesystemCounterHandler edge cases"""

    def test_init_with_none_info_dir(self):
        """Test that initializing with None info_dir raises ValueError"""
        with self.assertRaises(ValueError) as context:
            FilesystemCounterHandler(None)
        self.assertIn("required", str(context.exception))

    def test_init_with_empty_info_dir(self):
        """Test that initializing with empty info_dir raises ValueError"""
        with self.assertRaises(ValueError) as context:
            FilesystemCounterHandler("")
        self.assertIn("required", str(context.exception))

    def test_init_with_info_dir_with_separator(self):
        """Test initializing with info_dir that already has separator"""
        with tempfile.TemporaryDirectory() as temp_dir:
            info_dir_with_sep = temp_dir + os.sep
            handler = FilesystemCounterHandler(info_dir_with_sep)
            # Should not add another separator
            self.assertEqual(handler.info_dir, info_dir_with_sep)

    def test_set_counter_valid_value(self):
        """Test setting a valid counter value"""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            handler.set_counter(10, 'test_entity')
            result = handler.read_counter('test_entity')
            self.assertEqual(result, 10)

    def test_set_counter_negative_value(self):
        """Test that setting a negative value raises ValueError"""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            with self.assertRaises(ValueError) as context:
                handler.set_counter(-1, 'test_entity')
            self.assertIn("non negative integer", str(context.exception))

    def test_read_counter_nonexistent_entity(self):
        """Test reading a non-existent entity returns 0"""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            # First, create a file with one entity
            handler.set_counter(5, 'entity1')
            # Now read a different entity that doesn't exist
            result = handler.read_counter('nonexistent_entity')
            self.assertEqual(result, 0)

    def test_file_creation_on_first_use(self):
        """Test that file and directory are created on first use"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use a subdirectory that doesn't exist yet
            info_dir = os.path.join(temp_dir, 'subdir', 'counters')
            handler = FilesystemCounterHandler(info_dir)

            # Directory should not exist yet
            self.assertFalse(os.path.exists(info_dir))

            # Trigger file creation
            handler.set_counter(1, 'test_entity')

            # Directory and file should now exist
            self.assertTrue(os.path.exists(info_dir))
            prov_file = os.path.join(info_dir, 'provenance_index.json')
            self.assertTrue(os.path.isfile(prov_file))

    def test_increment_counter_new(self):
        """Test incrementing a new counter starts at 1"""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            result = handler.increment_counter('new_entity')
            self.assertEqual(result, 1)

    def test_increment_counter_existing(self):
        """Test incrementing an existing counter"""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FilesystemCounterHandler(temp_dir)
            handler.set_counter(5, 'existing_entity')
            result = handler.increment_counter('existing_entity')
            self.assertEqual(result, 6)


class TestSqliteCounterHandler(unittest.TestCase):
    """Test SqliteCounterHandler edge cases"""

    def test_set_counter_valid_value(self):
        """Test setting a valid counter value"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            handler.set_counter(10, 'test_entity')
            result = handler.read_counter('test_entity')
            self.assertEqual(result, 10)
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_set_counter_negative_value(self):
        """Test that setting a negative value raises ValueError"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            with self.assertRaises(ValueError) as context:
                handler.set_counter(-1, 'test_entity')
            self.assertIn("non negative integer", str(context.exception))
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_read_counter_nonexistent_entity(self):
        """Test reading a non-existent entity returns 0"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            # Set one entity
            handler.set_counter(5, 'entity1')
            # Read a different entity that doesn't exist
            result = handler.read_counter('nonexistent_entity')
            self.assertEqual(result, 0)
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_read_counter_database_corruption(self):
        """Test database corruption scenario with multiple rows for same entity"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)

            # Manually insert duplicate rows to simulate corruption
            # First, insert one entity normally
            handler.set_counter(5, 'test_entity')

            # Now manually insert another row with the same entity (bypassing PRIMARY KEY constraint by direct SQL)
            # This simulates a corrupted database state
            # Note: This is difficult to do with PRIMARY KEY constraint, so we'll test the exception path
            # by manually manipulating the database
            con = sqlite3.connect(temp_db_path)
            cur = con.cursor()

            # Drop the PRIMARY KEY constraint and recreate table without it
            cur.execute("DROP TABLE info")
            cur.execute("""CREATE TABLE info(entity TEXT, count INTEGER)""")

            # Insert duplicate entries
            import urllib.parse
            entity_encoded = urllib.parse.quote('test_entity')
            cur.execute(f"INSERT INTO info (entity, count) VALUES ('{entity_encoded}', 5)")
            cur.execute(f"INSERT INTO info (entity, count) VALUES ('{entity_encoded}', 10)")
            con.commit()
            con.close()

            # Now try to read - should raise exception
            with self.assertRaises(Exception) as context:
                handler.read_counter('test_entity')
            self.assertIn("more than one counter", str(context.exception))
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_increment_counter_new(self):
        """Test incrementing a new counter starts at 1"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            result = handler.increment_counter('new_entity')
            self.assertEqual(result, 1)
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_increment_counter_existing(self):
        """Test incrementing an existing counter"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        try:
            handler = SqliteCounterHandler(temp_db_path)
            handler.set_counter(5, 'existing_entity')
            result = handler.increment_counter('existing_entity')
            self.assertEqual(result, 6)
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)


if __name__ == '__main__':
    unittest.main()
