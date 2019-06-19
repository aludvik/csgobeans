import os
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from . import beans

SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
BEANS_FILE_PATH = os.path.join(os.path.dirname(__file__), "beans")


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
            bean_list = []
            for line in beans_file.readlines():
                split_line = line.split(';')
                assert len(split_line) == 4
                bean_list.append(beans.Bean(
                    split_line[0],
                    split_line[1],
                    int(split_line[2]),
                    int(split_line[3])))

        self.populate_beans(bean_list)

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

    # - Steam
    def associate_user_id_with_steam_id(self, user_id, steam_id):
        self.db.execute(
            'INSERT INTO steam (steam_id, user_id) VALUES (?, ?)',
            (steam_id, user_id))
        self.db.commit()

    def steam_id_from_user_id(self, user_id):
        return _unwrap_single_if_not_none(self.db.execute(
            'SELECT steam_id FROM steam WHERE user_id = ?',
            (user_id,)
        ).fetchone())

    # - Beans

    # Beans Accessors
    def list_beans_from_bean_ids(self, bean_ids):
        result = []

        for bean_id in bean_ids:
            row = self.db.execute(
                'SELECT bean_name, short_desc, color, quality'
                ' FROM beans WHERE bean_id = ?',
                (bean_id,)
            ).fetchone()
            if row is None:
                result.append(None)
            else:
                result.append(beans.Bean(*row))

        return result

    def list_beans(self, start=-1, count=-1):
        return [
            (row[0], beans.Bean(row[1], row[2], row[3], row[4]))
            for row in self.db.execute(
                'SELECT * FROM beans ORDER BY bean_name LIMIT ? OFFSET ?',
                (count, start)
            ).fetchall()
        ]

    # Beans Mutators
    def populate_beans(self, beans):
        self.db.executemany(
            'INSERT INTO beans (bean_name, short_desc, color, quality)'
            ' VALUES (?, ?, ?, ?)',
            [_bean_to_tuple(bean) for bean in beans])
        self.db.commit()

    # - Inventory

    # Inventory Accesors
    def list_inventory_from_user_id(self, user_id, start=-1, count=-1):
        return [
            (row[0], row[1], beans.Bean(row[2], row[3], row[4], row[5]))
            for row in self.db.execute(
                'SELECT'
                ' inventory.bean_id, qty, bean_name,'
                ' short_desc, color, quality'
                ' FROM inventory'
                ' JOIN beans ON inventory.bean_id = beans.bean_id'
                ' WHERE user_id = ?'
                ' ORDER BY bean_name'
                ' LIMIT ? OFFSET ?',
                (user_id, count, start)
            ).fetchall()
        ]

    # Inventory Mutators
    def give_user_id_beans(self, user_id, beans):
        cursor = self.db.cursor()
        for bean_id, qty in beans:
            self.__give_user_id_bean(cursor, user_id, bean_id, qty)
        cursor.close()
        self.db.commit()

    def __give_user_id_bean(self, cursor, user_id, bean_id, qty):
        prev_qty = _unwrap_single_if_not_none(cursor.execute(
            'SELECT qty FROM inventory WHERE user_id = ? AND bean_id = ?',
            (user_id, bean_id)
        ).fetchone())
        if prev_qty is None:
            cursor.execute(
                'INSERT INTO inventory (user_id, bean_id, qty)'
                ' VALUES (?, ?, ?)',
                (user_id, bean_id, qty))
        else:
            cursor.execute(
                'UPDATE inventory SET qty = ?'
                ' WHERE user_id = ? AND bean_id = ?',
                (prev_qty + qty, user_id, bean_id))

    # - Trades

    # Trade Accessors
    def list_trades_from_user_id(self, user_id, start=-1, count=-1):
        return [
            tuple(row)
            for row in self.db.execute(
                'SELECT'
                ' trade_id, item, trade_timestamp'
                ' FROM trades'
                ' WHERE user_id = ?'
                ' ORDER BY trade_timestamp'
                ' LIMIT ? OFFSET ?',
                (user_id, count, start)
            ).fetchall()
        ]

    def already_traded(self, user_id, item):
        traded = self.db.execute(
            'SELECT trade_id FROM trades WHERE user_id = ? AND item = ?',
            (user_id, item)
        ).fetchone()
        return traded is not None

    # Trade Mutators
    def record_trade(self, user_id, item):
        self.db.execute(
            'INSERT INTO trades (user_id, item) VALUES (?, ?)',
            (user_id, item))
        self.db.commit()


def _unwrap_single_if_not_none(single):
    if single is not None:
        assert len(single) == 1
        return single[0]


def _bean_to_tuple(bean):
    return (bean.name, bean.short_desc, bean.color.value, bean.quality.value)
