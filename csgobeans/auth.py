import flask
from werkzeug.security import check_password_hash, generate_password_hash

from . import ctx
from . import db
from .decorators import get_template_or_post_with_err
from .decorators import redirect_on_err
from .decorators import FlashError


def create_blueprint():
    bp = flask.Blueprint('auth', __name__)

    @bp.route("/register", methods=['GET', 'POST'])
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
        ctx.logger().info("Registered new user '%s'", form['username'])
        return flask.redirect(flask.url_for('index'))

    @bp.route("/login", methods=['POST'])
    @redirect_on_err('beans')
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

        ctx.logger().debug("User logged in '%s'", user['username'])

        return flask.redirect(flask.url_for('index'))

    @bp.route("/logout", methods=['POST'])
    @redirect_on_err('index')
    def logout():
        flask.session.clear()
        return flask.redirect(flask.url_for('index'))

    return bp
