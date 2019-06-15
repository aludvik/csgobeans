import flask

from . import ctx
from . import db
from .decorators import get_template_or_post_with_err
from .decorators import redirect_on_err
from .decorators import login_required
from .decorators import FlashError


def create_blueprint():
    bp = flask.Blueprint('inventory', __name__)

    @bp.route("/beans")
    @login_required
    def beans():
        db = ctx.get_db()
        user_id = ctx.get_user_id()
        beans = db.list_inventory_from_user_id(user_id)
        return ctx.render_template_with_context("beans.html", beans=beans)

    @bp.route("/trade", methods=['GET', 'POST'])
    @login_required
    @redirect_on_err("inventory.trade")
    def trade():
        if flask.request.method == 'GET':
            db = ctx.get_db()
            beans = db.list_beans()
            return ctx.render_template_with_context("trade.html", beans=beans)

        if flask.request.method == 'POST':
            form = flask.request.form
            try:
                bean_id = int(form["bean_id"])
            except:
                raise FlashError("Invalid Bean ID")
            try:
                qty = int(form["qty"])
            except:
                raise FlashError("Invalid Quantity")

            if not form["item"]:
                raise FlashError("Invalid Item")

            item = form["item"]

            user_id = ctx.get_user_id()
            db = ctx.get_db()

            if db.already_traded(user_id, item):
                raise FlashError("Already traded")

            db.give_user_id_beans(user_id, [(bean_id, qty)])
            db.record_trade(user_id, item)

            return flask.redirect(flask.url_for("inventory.trade"))

    @bp.route("/history")
    @login_required
    def history():
        db = ctx.get_db()
        trades = db.list_trades_from_user_id(ctx.get_user_id())
        return ctx.render_template_with_context("history.html", trades=trades)

    return bp
