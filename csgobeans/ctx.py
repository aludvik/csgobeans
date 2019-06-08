import os

from flask import current_app, g

from .db import Database


def app_local_path(app, path):
    return os.path.join(app.instance_path, path)


def database_local_path(app):
    return app_local_path(app, app.config['DATABASE_FILE'])


def get_db():
    if 'db' not in g:
        g.db = Database(database_local_path(current_app))
    return g.db


def teardown_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def register_teardowns(app):
    app.teardown_appcontext(teardown_db)
