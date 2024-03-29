import os

from flask import current_app, g, session, render_template

from .db import Database


def render_template_with_context(template, **kwargs):
    username = get_username()
    return render_template(
        template,
        username=username,
        **kwargs)


def logger():
    return current_app.logger


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


def get_username():
    user_id = get_user_id()
    if user_id is None:
        return None

    if 'username' not in g:
        db = get_db()
        g.username = db.username_from_user_id(user_id)

    return g.username


def register_teardowns(app):
    app.teardown_appcontext(teardown_db)
