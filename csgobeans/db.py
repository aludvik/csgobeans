import os
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from . import beans

SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
BEANS_FILE_PATH = os.path.join(os.path.dirname(__file__), "beans")


def _bean_to_tuple(bean):
    return (bean.name, bean.short_desc, bean.color.value, bean.quality.value)


def _tuple_to_bean_or_none(tuple):
    if tuple is None:
        return None

    return beans.Bean(
        tuple[1],
        tuple[2],
        beans.Color(tuple[3]),
        beans.Quality(tuple[4]))

def _user_tuple_to_dict_or_none(tuple):
    if tuple is None:
        return None

    return {
        'user_id': tuple[0],
        'username': tuple[1],
        'password': tuple[2]
    }


class Database:
    def initialize_from_schema(
        self,
        schema_file_path=SCHEMA_FILE_PATH
    ):
        with open(schema_file_path, encoding='utf-8') as schema_file:
            schema = schema_file.read()
            self.db.executescript(schema)

    def populate_beans_from_file(
        self,
        beans_file_path=BEANS_FILE_PATH
    ):
        with open(beans_file_path, encoding='utf-8') as beans_file:
            for line in beans_file.readlines():
                split_line = line.split(';')
                assert len(split_line) == 4
                bean = beans.Bean(
                    split_line[0],
                    split_line[1],
                    int(split_line[2]),
                    int(split_line[3]))
                self.create_bean(bean)

    def __init__(self, database_file_path):
        self.db = sqlite3.connect(
            database_file_path,
            detect_types=sqlite3.PARSE_DECLTYPES)

    def close(self):
        self.db.close()

    def closed(self):
        try:
            self.db.cursor()
        except sqlite3.ProgrammingError:
            return True
        return False

    # - Auth
    # Look up information about a user from the id or username
    # Register a new user

    # Auth Accessors
    def username_from_user_id(self, user_id):
        return _unwrap_single_if_not_none(self.db.execute(
            'SELECT username FROM auth WHERE user_id = ?',
            (user_id,)
        ).fetchone())

    def check_username_and_password(self, username, password):
        user_id_and_password_hash = self.db.execute(
            'SELECT user_id, password_hash FROM auth WHERE username = ?',
            (username,)
        ).fetchone()

        if user_id_and_password_hash is None:
            return None

        user_id, password_hash = user_id_and_password_hash
        if not check_password_hash(password_hash, password):
            return None

        return user_id

    # Auth Mutators
    def register_user(self, username, password):
        password_hash = generate_password_hash(password)
        self.db.execute(
            'INSERT INTO auth (username, password_hash) VALUES (?, ?)',
            (username, password_hash))
        self.db.commit()

    # - Beans
    # Look up information about a bean from its id
    # Create new beans

    # Beans Accessors
    def bean_from_name(self, bean_name):
        return _tuple_to_bean_or_none(self.db.execute(
            'SELECT * FROM beans WHERE bean_name = ?', (bean_name,)
        ).fetchone())

    def bean_from_bean_id(self, bean_id):
        return _tuple_to_bean_or_none(self.db.execute(
            'SELECT * FROM beans WHERE bean_id = ?', (bean_id,)
        ).fetchone())

    def bean_id_from_name(self, bean_name):
        return _unwrap_single_if_not_none(self.db.execute(
            'SELECT bean_id FROM beans WHERE bean_name = ?', (bean_name,)
        ).fetchone())

    def list_beans(self):
        return self.db.execute(
            'SELECT bean_id, bean_name FROM beans ORDER BY bean_name'
        ).fetchall()

    # Beans Mutators
    def create_bean(self, bean):
        self.db.execute(
            'INSERT INTO beans (bean_name, short_desc, color, quality)'
            ' VALUES (?, ?, ?, ?)',
            _bean_to_tuple(bean))
        self.db.commit()

    # - Inventory
    # Look up a user's inventory from the user id
    # Page through a user's inventory
    # Add to a user's inventory

    # Inventory Accesors
    def inventory_from_user_id(self, user_id, start=-1, count=-1):
        return self.db.execute(
            'SELECT * FROM inventory WHERE user_id = ? LIMIT ? OFFSET ?',
            (user_id, count, start)
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
        if qty is None:
            self.init_bean_id_qty_for_user_id(user_id, bean_id, inc_qty)
            return

        qty += inc_qty
        self.db.execute(
            'UPDATE inventory SET qty = ? WHERE user_id = ? AND bean_id = ?',
            (qty, user_id, bean_id))
        self.db.commit()

    # - Trades
    # Log trades and timestamps
    # Lookup whether an item has been traded previously by a given user
    # Page through a user's trades

    # Trade Accessors
    def already_traded(self, user_id, item):
        traded = self.db.execute(
            'SELECT trade_id FROM trades WHERE user_id = ? AND item = ?',
            (user_id, item)
        ).fetchone()
        return traded is not None

    def trades_from_user_id(self, user_id, start=-1, count=-1):
        return self.db.execute(
            'SELECT * FROM trades WHERE user_id = ?'
            ' ORDER BY trade_timestamp'
            ' LIMIT ? OFFSET ?',
            (user_id, count, start)
        ).fetchall()

    # Trade Mutators
    def log_trade(self, user_id, item):
        self.db.execute(
            'INSERT INTO trades (user_id, item) VALUES (?, ?)',
            (user_id, item))
        self.db.commit()


def _unwrap_single_if_not_none(single):
    if single is not None:
        assert len(single) == 1
        return single[0]
