import random
import requests

import flask

from . import ctx
from . import db
from .decorators import get_template_or_post_with_err
from .decorators import redirect_on_err
from .decorators import login_required
from .decorators import FlashError


CSGO_INVENTORY_URL =\
    "https://steamcommunity.com/profiles/%s/inventory/json/730/2"


def load_csgo_inventory(steam_id):
    response = requests.get(CSGO_INVENTORY_URL % steam_id)

    if response.status_code == 429:
        return ([], True, response.headers.get("Retry-After", -1))

    response_json = response.json()
    success = response_json.get("success", None)
    assert success is not None and success
    inventory = response_json.get("rgInventory", None)
    assert inventory is not None
    descriptions = response_json.get("rgDescriptions", None)
    assert descriptions is not None
    assert len(inventory) == len(descriptions)

    def extract(item):
        id = item.get("id", None)
        assert id is not None
        classid = item.get("classid", None)
        assert classid is not None
        instanceid = item.get("instanceid", None)
        assert instanceid is not None
        desc_key = classid + "_" + instanceid
        name = descriptions[desc_key].get("market_name", None)
        assert name is not None
        return (id, name)

    return (list(map(extract, inventory.values())), False, 0)


def pick_random_bean_and_qty(beans):
    bean_id, bean = random.choice(beans)
    qty = random.randint(1, 9)
    return (bean_id, bean, qty)


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
            steam_id = ctx.get_username()
            inventory, too_many, retry_after = load_csgo_inventory(steam_id)
            return ctx.render_template_with_context(
                "trade.html",
                csgo_inventory=inventory,
                too_many=too_many,
                retry_after=retry_after)

        if flask.request.method == 'POST':
            form = flask.request.form

            item_id = None
            try:
                item_id = form["item_id"]
            except:
                raise FlashError("Invalid Item Id")

            item_name = None
            try:
                item_name = form["item_name"]
            except:
                raise FlashError("Invalid Item Name")

            user_id = ctx.get_user_id()
            db = ctx.get_db()
            if db.already_traded(user_id, item_id):
                raise FlashError("Already traded")

            beans = db.list_beans()
            bean_id, bean, qty = pick_random_bean_and_qty(beans)
            db.give_user_id_beans(user_id, [(bean_id, qty)])
            db.record_trade(user_id, item_id)

            flask.flash(
                "Congratulations! You traded {} for {} {}".format(
                item_name, qty, bean))

            return flask.redirect(flask.url_for("inventory.trade"))

    @bp.route("/history")
    @login_required
    def history():
        db = ctx.get_db()
        trades = db.list_trades_from_user_id(ctx.get_user_id())
        return ctx.render_template_with_context("history.html", trades=trades)

    return bp
