import os

import flask
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from . import ctx
from . import auth


def create_app(test_config=None):
    app = flask.Flask(__name__, instance_relative_config=True)

    configure(app)
    setup(app)

    @app.route("/")
    def index():
        return ctx.render_template_with_context("index.html")

    app.register_blueprint(auth.create_blueprint())

    @app.route("/inventory")
    def inventory():
        return ctx.render_template_with_context("inventory.html")

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
