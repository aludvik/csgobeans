import flask

class FlashError(BaseException):
    def __init__(self, msg):
        self.msg = msg


def flash_error(msg):
    flask.flash(msg, 'danger')


def flash_warning(msg):
    flask.flash(msg, 'warning')


def flash_success(msg):
    flask.flash(msg, 'success')


def flash_neutral(msg):
    flask.flash(msg)
