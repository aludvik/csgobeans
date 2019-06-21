import flask

from . import ctx
from .flash import *


def redirect_on_err(redirect):
    def wrapper(f):
        def decorator():
            try:
                return f()
            except FlashError as error:
                flash_error(error.msg)
                return flask.redirect(flask.url_for(redirect))
        decorator.__name__ = f.__name__
        return decorator
    return wrapper


def login_required(f):
    def decorator():
        if ctx.get_user_id() is None:
            flask_warning("Login required")
            return flask.redirect(flask.url_for('index'))
        return f()
    decorator.__name__ = f.__name__
    return decorator
