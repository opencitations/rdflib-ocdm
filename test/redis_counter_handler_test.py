#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch

import fakeredis

from rdflib_ocdm.counter_handler.redis_counter_handler import \
    RedisCounterHandler


class TestRedisCounterHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_redis = fakeredis.FakeStrictRedis()
        
    def setUp(self):
        self.fake_redis.flushall()
        self.redis_patcher = patch('redis.Redis', return_value=self.fake_redis)
        self.mock_redis = self.redis_patcher.start()
        
        self.handler = RedisCounterHandler(host='localhost', port=6379, db=0)
        self.handler.connect()
    
    def tearDown(self):
        self.handler.disconnect()
        self.redis_patcher.stop()
    
    def test_set_counter_valid_value(self):
        """Test setting a valid counter value"""
        self.handler.set_counter(10, 'test_entity')
        result = self.fake_redis.get('test_entity')
        self.assertEqual(int(result), 10)
    
    def test_set_counter_negative_value(self):
        """Test that setting a negative value raises ValueError"""
        with self.assertRaises(ValueError):
            self.handler.set_counter(-1, 'test_entity')
    
    def test_read_counter_existing(self):
        """Test reading an existing counter"""
        self.fake_redis.set('test_entity', 5)
        result = self.handler.read_counter('test_entity')
        self.assertEqual(result, 5)
    
    def test_read_counter_nonexistent(self):
        """Test reading a non-existent counter returns 0"""
        result = self.handler.read_counter('nonexistent_entity')
        self.assertEqual(result, 0)
    
    def test_increment_counter_new(self):
        """Test incrementing a new counter starts at 1"""
        result = self.handler.increment_counter('new_entity')
        self.assertEqual(result, 1)
        self.assertEqual(int(self.fake_redis.get('new_entity')), 1)
    
    def test_increment_counter_existing(self):
        """Test incrementing an existing counter"""
        self.fake_redis.set('existing_entity', 5)
        result = self.handler.increment_counter('existing_entity')
        self.assertEqual(result, 6)
        self.assertEqual(int(self.fake_redis.get('existing_entity')), 6)
    
    def test_flush(self):
        """Test flushing the database"""
        self.fake_redis.set('entity1', 1)
        self.fake_redis.set('entity2', 2)
        self.handler.flush()
        self.assertIsNone(self.fake_redis.get('entity1'))
        self.assertIsNone(self.fake_redis.get('entity2'))
    
    def test_disconnect_no_connection(self):
        """Test disconnecting when no connection exists"""
        handler = RedisCounterHandler(host='localhost', port=6379, db=0)
        handler.disconnect()
        handler.disconnect()

if __name__ == '__main__':
    unittest.main()
