import flask

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
