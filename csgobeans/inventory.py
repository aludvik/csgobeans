import flask

from . import ctx
from . import db
from .decorators import get_template_or_post_with_err
from .decorators import redirect_on_err


def create_blueprint():
    bp = flask.Blueprint('inventory', __name__)

    @bp.route("/beans")
    def inventory():
        return ctx.render_template_with_context("beans.html")

    return bp
