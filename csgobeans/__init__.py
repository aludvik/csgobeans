import os

import flask
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from . import ctx


class FlashError(BaseException):
    def __init__(self, msg):
        self.msg = msg


def redirect_on_err(redirect):
    def wrapper(f):
        def decorator():
            try:
                return f()
            except FlashError as error:
                flask.flash(error.msg)
                return flask.redirect(url_for(redirect))
        decorator.__name__ = f.__name__
        return decorator
    return wrapper


def login_required(f):
    def decorator(*args, **kwargs):
        if ctx.get_user_id() is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    decorator.__name__ = f.__name__
    return decorator


def get_template_or_post_with_err(template):
    def wrapper(f):
        def decorator():
            if flask.request.method == 'POST':
                try:
                    return f()
                except FlashError as error:
                    flask.flash(error.msg)
            return render_template_with_context(template)
        decorator.__name__ = f.__name__
        return decorator
    return wrapper


def render_template_with_context(template):
    user = ctx.get_user()
    if user is None:
        return flask.render_template(template)
    return flask.render_template(
        template,
        username=user['username'])


def create_app(test_config=None):
    app = flask.Flask(__name__, instance_relative_config=True)

    configure(app)
    setup(app)

    @app.route("/")
    def index():
        return render_template_with_context("index.html")

    @app.route("/register", methods=['GET', 'POST'])
    def register():
        if flask.request.method == 'POST':
            username = flask.request.form['username']
            password = flask.request.form['password']
            db = ctx.get_db()
            error = None

            if not username:
                error = 'Username is required'
            elif not password:
                error = 'Password is required'
            elif db.user_id_from_username(username) is not None:
                error = 'User {} is already registered.'.format(username)

            if error is None:
                db.register_user(username, generate_password_hash(password))
                app.logger.info("Registered new user '%s'", username)
                return flask.redirect(flask.url_for('inventory'))

            flask.flash(error)

        return flask.render_template('register.html')

    @app.route("/inventory")
    def inventory():
        return flask.render_template("inventory.html")

    return app

def configure(app):
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE_FILE='csgobeans.sqlite',
    )

def setup(app):
    os.makedirs(app.instance_path, exist_ok=True)
    if not os.path.isfile(ctx.database_local_path(app)):
        db.Database(ctx.database_local_path(app)).initialize_from_schema()
        # TODO: Populate with beans
    ctx.register_teardowns(app)
