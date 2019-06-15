import os
import tempfile
import unittest

import sqlite3

from csgobeans.db import Database
from csgobeans.beans import Bean, Color, Quality


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
        beans = [
            Bean(*args)
            for args in sorted([
                ("a", "a", 1, 1),
                ("b", "b", 2, 2),
                ("c", "c", 3, 3),
                ("d", "d", 4, 4),
            ])
        ]

        self.db.populate_beans(beans)

        bean_ids = []
        for i, (bean_id, bean) in enumerate(self.db.list_beans()):
            self.assertEqual(beans[i], bean)
            bean_ids.append(bean_id)

        for i, (bean_id, bean) in enumerate(
            self.db.list_beans(start=1, count=2)
        ):
            self.assertEqual(beans[i+1], bean)

        with self.assertRaises(sqlite3.IntegrityError):
            self.db.populate_beans(beans)

        for i, bean in enumerate(self.db.list_beans_from_bean_ids(bean_ids)):
            self.assertEqual(beans[i], bean)

        bean_ids[1] = 999
        self.assertEqual(None, self.db.list_beans_from_bean_ids(bean_ids)[1])

    def test_inventory(self):
        self.db.register_user("test", "test")
        user_id = self.db.check_username_and_password("test", "test")

        beans = [
            Bean(*args)
            for args in sorted([
                ("a", "a", 1, 1),
                ("b", "b", 2, 2),
                ("c", "c", 3, 3),
                ("d", "d", 4, 4),
            ])
        ]
        self.db.populate_beans(beans)

        bean_ids = [bid for bid, _ in self.db.list_beans(count=2)]
        self.db.give_user_id_beans(
            user_id,
            [(bid, qty+1) for qty, bid in enumerate(bean_ids)])

        inventory = self.db.list_inventory_from_user_id(user_id)

        for i, (bean_id, qty, bean) in enumerate(inventory):
            self.assertEqual(bean_ids[i], bean_id)
            self.assertEqual(i + 1, qty)
            self.assertEqual(beans[i], bean)

    def test_trades(self):
        self.db.register_user("test", "test")
        user_id = self.db.check_username_and_password("test", "test")

        self.db.record_trade(user_id, "item")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.record_trade(user_id, "item")

        trades = self.db.list_trades_from_user_id(user_id)
        self.assertEqual(1, len(trades))
        trade_id, item, timestamp = trades[0]
        self.assertEqual("item", item)

        self.assertTrue(self.db.already_traded(user_id, "item"))
        self.assertFalse(self.db.already_traded(user_id, "notitem"))
