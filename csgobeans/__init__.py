import os

import flask
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from . import ctx


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
    @get_template_or_post_with_err('register.html')
    def register():
        form = flask.request.form
        db = ctx.get_db()

        if not form['username']:
            raise FlashError('Username is required')
        elif not form['password']:
            raise FlashError('Password is required')
        elif db.user_id_from_username(form['username']) is not None:
            raise FlashError(
                'User {} is already registered.'.format(form['username']))

        db.register_user(
            form['username'],
            generate_password_hash(form['password']))
        app.logger.info("Registered new user '%s'", form['username'])
        return flask.redirect(flask.url_for('index'))

    @app.route("/login", methods=['POST'])
    @redirect_on_err('inventory')
    def login():
        form = flask.request.form
        db = ctx.get_db()

        user = db.user_from_username(form['username'])
        if user is None:
            raise FlashError('Incorrect username')
        elif not check_password_hash(user['password'], form['password']):
            raise FlashError('Incorrect password')

        ctx.clear_session()
        ctx.set_user_id(user['user_id'])

        app.logger.debug("User logged in '%s'", user['username'])

        return flask.redirect(flask.url_for('index'))

    @app.route("/logout", methods=['POST'])
    @redirect_on_err('index')
    def logout():
        flask.session.clear()
        return flask.redirect(flask.url_for('index'))

    @app.route("/inventory")
    def inventory():
        return render_template_with_context("inventory.html")

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
