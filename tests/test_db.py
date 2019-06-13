import os
import tempfile
import unittest

import sqlite3

from csgobeans.db import Database
from csgobeans.beans import Bean, Color, Quality

TEST_USER = {"user": "test", "password": "hash"}
TEST_BEAN = Bean("test", "A testy bean", Color.GREY, Quality.COMMON)
TEST_ITEM = "testitem"

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
        user_id = self.db.check_username_and_password("abc", "def")
        self.assertIsNot(user_id, None)
        username = self.db.username_from_user_id(user_id)
        self.assertEqual("abc", username)

        self.assertIs(None, self.db.check_username_and_password("abc", "ghi"))

        with self.assertRaises(sqlite3.IntegrityError):
            self.db.register_user("abc", "ghi")

        self.assertEqual(
            None,
            self.db.check_username_and_password("jkl", "mno"))

    def test_beans(self):
        self.db.create_bean(TEST_BEAN)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.create_bean(TEST_BEAN)
        test_id = self.db.bean_id_from_name(TEST_BEAN.name)
        test2 = self.db.bean_from_name(TEST_BEAN.name)
        self.assertEqual(TEST_BEAN, test2)
        test3 = self.db.bean_from_bean_id(test_id)
        self.assertEqual(TEST_BEAN, test3)

        beans = self.db.list_beans()
        self.assertEqual(1, len(beans))
        self.assertEqual((test_id, TEST_BEAN.name), beans[0])

    def test_inventory(self):
        self.db.register_user(TEST_USER["user"], TEST_USER["password"])
        user_id = self.db.check_username_and_password(
            TEST_USER["user"], TEST_USER["password"])
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

    def test_inventory_paging(self):
        self.db.register_user(TEST_USER["user"], TEST_USER["password"])
        user_id = self.db.check_username_and_password(
            TEST_USER["user"], TEST_USER["password"])
        for i in range(1, 101):
            bean = Bean(str(i), "bean " + str(i), Color.RED, Quality.RARE)
            self.db.create_bean(bean)
        beans = self.db.inventory_from_user_id(user_id, start=10, count=5)
        for i, bean in enumerate(beans):
            self.assertEqual(i + start, int(beans[i].name))

    def test_trades(self):
        self.db.register_user(TEST_USER["user"], TEST_USER["password"])
        self.db.log_trade(TEST_USER["user"], TEST_ITEM)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.log_trade(TEST_USER["user"], TEST_ITEM)

        trades = self.db.trades_from_user_id(TEST_USER["user"])
        self.assertEqual(1, len(trades))
        trade_id, user_id, item, timestamp = trades[0]
        self.assertEqual(user_id, TEST_USER["user"])
        self.assertEqual(item, TEST_ITEM)

        self.assertTrue(self.db.already_traded(user_id, TEST_ITEM))
        self.assertFalse(self.db.already_traded(user_id, "notanitem"))
