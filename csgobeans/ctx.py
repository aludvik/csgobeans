import os

from flask import current_app, g, session

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


def clear_session():
    session.clear()


def set_user_id(user_id):
    session['user_id'] = user_id


def get_user_id():
    if 'user_id' not in session:
        return None
    return session['user_id']


def get_user():
    user_id = get_user_id()
    if user_id is None:
        return None

    if 'user' not in g:
        db = get_db()
        g.user = db.user_from_user_id(user_id)

    return g.user


def register_teardowns(app):
    app.teardown_appcontext(teardown_db)
