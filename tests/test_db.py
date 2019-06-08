import os
import tempfile
import unittest

import sqlite3

from csgobeans.db import Database
from csgobeans.beans import Bean, Color, Quality

TEST_USER = {"user": "test", "password": "hash"}
TEST_BEAN = Bean("test", "A testy bean", Color.GREY, Quality.COMMON)

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_dir = tempfile.mkdtemp()
        self.db_file_path = os.path.join(self.db_dir, 'testdb.sql')
        self.db = Database(self.db_file_path)
        self.db.initialize_from_schema()

    def tearDown(self):
        self.db.close()
        os.remove(self.db_file_path)
        os.rmdir(self.db_dir)

    def test_initialize(self):
        """Just run the fixture code."""

    def test_user_registration(self):
        self.db.register_user("abc", "def")
        user_id, username, hash = self.db.user_from_username("abc")
        self.assertEqual("abc", username)
        self.assertEqual("def", hash)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.register_user("abc", "ghi")

        self.assertEqual(None, self.db.user_from_username("jkl"))
        self.assertEqual(None, self.db.user_id_from_username("jkl"))

        user_id2, username2, hash2 = self.db.user_from_user_id(user_id)
        self.assertEqual(user_id, user_id2)
        self.assertEqual("abc", username2)
        self.assertEqual("def", hash2)

        user_id3 = self.db.user_id_from_username("abc")
        self.assertEqual(user_id, user_id3)

    def test_beans(self):
        self.db.create_bean(TEST_BEAN)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.create_bean(TEST_BEAN)
        test_id = self.db.bean_id_from_name(TEST_BEAN.name)
        test2 = self.db.bean_from_name(TEST_BEAN.name)
        self.assertEqual(TEST_BEAN, test2)
        test3 = self.db.bean_from_bean_id(test_id)
        self.assertEqual(TEST_BEAN, test3)

    def test_inventory(self):
        self.db.register_user(TEST_USER["user"], TEST_USER["password"])
        user_id = self.db.user_id_from_username(TEST_USER["user"])
        self.db.create_bean(TEST_BEAN)
        bean_id = self.db.bean_id_from_name(TEST_BEAN.name)

        self.db.init_bean_id_qty_for_user_id(user_id, bean_id, 3)
        self.assertEqual(3, self.db.bean_id_qty_for_user_id(user_id, bean_id))

        with self.assertRaises(sqlite3.IntegrityError):
            self.db.init_bean_id_qty_for_user_id(user_id, bean_id, 5)
        self.assertEqual(3, self.db.bean_id_qty_for_user_id(user_id, bean_id))

        self.db.inc_bean_id_qty_for_user_id(user_id, bean_id, 2)
        self.assertEqual(5, self.db.bean_id_qty_for_user_id(user_id, bean_id))

        navy = Bean("navy", "A sailing bean", Color.WHITE, Quality.UNCOMMON)
        self.db.create_bean(navy)
        navy_id = self.db.bean_id_from_name("navy")
        self.db.init_bean_id_qty_for_user_id(user_id, navy_id, 2000)
