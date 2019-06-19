import json
import requests
import urllib

import flask

from . import ctx
from . import db
from .decorators import get_template_or_post_with_err
from .decorators import redirect_on_err
from .decorators import FlashError


OPENID_NS = "http://specs.openid.net/auth/2.0"
OPENID_SPEC = "http://specs.openid.net/auth/2.0/identifier_select"
STEAM_OPENID_URL = 'https://steamcommunity.com/openid/login'


def steam_auth_url(host, base_url):
    return STEAM_OPENID_URL + "?" + urllib.parse.urlencode({
        'openid.ns': OPENID_NS,
        'openid.identity': OPENID_SPEC,
        'openid.claimed_id': OPENID_SPEC,
        'openid.mode': 'checkid_setup',
        'openid.return_to': base_url,
    })


def validate_login(login_info):
    data = dict()
    data.update(login_info)
    data["openid.mode"] = "check_authentication"
    response = requests.post(STEAM_OPENID_URL, data=data)

    if "is_valid:true" in response.text:
        return True

    return False


def create_blueprint():
    bp = flask.Blueprint('auth', __name__)

    @bp.route("/login", methods=["GET", "POST"])
    def login():
        identity = flask.request.args.get('openid.identity', None)
        if identity is None:
            return flask.redirect(
                steam_auth_url(flask.request.host, flask.request.base_url))

        if not validate_login(flask.request.args):
            flask.flash("Login failed")
            return flask.redirect(flask.url_for('index'))

        steam_id = identity.split('/')[-1]

        db = ctx.get_db()
        user_id = db.check_username_and_password(steam_id, "")
        if user_id is None:
            db.register_user(steam_id, "")
            user_id = db.check_username_and_password(steam_id, "")
            db.associate_user_id_with_steam_id(user_id, steam_id)

        ctx.clear_session()
        ctx.set_user_id(user_id)

        flask.flash("Logged in with Steam ID %s" % steam_id)
        ctx.logger().debug("User logged in '%s'", steam_id)

        return flask.redirect(flask.url_for('index'))

    @bp.route("/logout", methods=['GET', 'POST'])
    @redirect_on_err('index')
    def logout():
        flask.session.clear()
        flask.flash("Logged out")
        return flask.redirect(flask.url_for('index'))

    return bp
