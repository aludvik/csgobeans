import os
import sqlite3

from . import beans

# - Trades
# Log trades and timestamps
# Lookup whether an item has been traded previously by a given user
# Page through a user's trades

SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

class Database:
    @staticmethod
    def connect_to_database(database_file_path):
        return sqlite3.connect(
            database_file_path,
            detect_types=sqlite3.PARSE_DECLTYPES)

    def initialize_from_schema(
        self,
        schema_file_path=SCHEMA_FILE_PATH
    ):
        with open(schema_file_path, encoding='utf-8') as schema_file:
            schema = schema_file.read()
            self.db.executescript(schema)

    def __init__(self, database_file_path):
        self.db = self.connect_to_database(database_file_path)

    def close(self):
        self.db.close()

    # - Auth
    # Look up information about a user from the id or username
    # Register a new user

    # Auth Accessors
    def user_from_user_id(self, user_id):
        return self.db.execute(
            'SELECT * FROM auth WHERE user_id = ?', (user_id,)
        ).fetchone()

    def user_from_username(self, username):
        return self.db.execute(
            'SELECT * FROM auth WHERE username = ?', (username,)
        ).fetchone()

    def user_id_from_username(self, username):
        return _unwrap_single_if_not_none(self.db.execute(
            'SELECT user_id FROM auth WHERE username = ?', (username,)
        ).fetchone())

    # Auth Mutators
    def register_user(self, username, password_hash):
        self.db.execute(
            'INSERT INTO auth (username, password) VALUES (?, ?)',
            (username, password_hash))
        self.db.commit()

    # - Beans
    # Look up information about a bean from its id
    # Create new beans

    # Beans Accessors
    def bean_from_name(self, bean_name):
        return beans.Bean.from_tuple_or_none(self.db.execute(
            'SELECT * FROM beans WHERE name = ?', (bean_name,)
        ).fetchone())

    def bean_from_bean_id(self, bean_id):
        return beans.Bean.from_tuple_or_none(self.db.execute(
            'SELECT * FROM beans WHERE bean_id = ?', (bean_id,)
        ).fetchone())

    def bean_id_from_name(self, bean_name):
        return _unwrap_single_if_not_none(self.db.execute(
            'SELECT bean_id FROM beans WHERE name = ?', (bean_name,)
        ).fetchone())

    # Beans Mutators
    def create_bean(self, bean):
        self.db.execute(
            'INSERT INTO beans (name, short_desc, color, quality)'
            ' VALUES (?, ?, ?, ?)',
            (bean.name, bean.short_desc, bean.color.value, bean.quality.value))
        self.db.commit()

    # - Inventory
    # Look up a user's inventory from the user id
    # Page through a user's inventory
    # Add to a user's inventory

    # Inventory Accesors
    def inventory_from_user_id(self, user_id, start=-1, count=-1):
        return self.db.execute(
            'SELECT * FROM inventory WHERE user_id = ?'
            ' ORDER BY inventory_id'
            ' LIMIT ? OFFSET ?',
            (user_id, count, offset)
        ).fetchall()

    def bean_id_qty_for_user_id(self, user_id, bean_id):
        return _unwrap_single_if_not_none(self.db.execute(
            'SELECT qty FROM inventory WHERE user_id = ? AND bean_id = ?',
            (user_id, bean_id)
        ).fetchone())

    # Inventory Mutators
    def init_bean_id_qty_for_user_id(self, user_id, bean_id, qty):
        self.db.execute(
            'INSERT INTO inventory (user_id, bean_id, qty) VALUES (?, ?, ?)',
            (user_id, bean_id, qty))
        self.db.commit()

    def inc_bean_id_qty_for_user_id(self, user_id, bean_id, inc_qty):
        qty = self.bean_id_qty_for_user_id(user_id, bean_id)
        qty += inc_qty
        self.db.execute(
            'UPDATE inventory SET qty = ? WHERE user_id = ? AND bean_id = ?',
            (qty, user_id, bean_id))
        self.db.commit()

def _unwrap_single_if_not_none(single):
    if single is not None:
        assert len(single) == 1
        return single[0]
