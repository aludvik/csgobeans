import flask
from werkzeug.security import check_password_hash, generate_password_hash

from . import cli
from . import ctx
from . import auth
from . import inventory


def create_app(test_config=None):
    app = flask.Flask(__name__, instance_relative_config=True)

    configure(app)
    setup(app)

    @app.route("/")
    def index():
        return ctx.render_template_with_context("index.html")

    app.register_blueprint(auth.create_blueprint())
    app.register_blueprint(inventory.create_blueprint())

    return app


def configure(app):
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE_FILE='csgobeans.sqlite',
    )

def setup(app):
    cli.init_cli(app)
    ctx.register_teardowns(app)
