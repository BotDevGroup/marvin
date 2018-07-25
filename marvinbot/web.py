from flask import Flask, g, redirect, url_for, request
from flask import appcontext_pushed, session
from datetime import timedelta
from flask_login import LoginManager, current_user
from flask.json import jsonify
from marvinbot.log import configure_logging
from marvinbot.utils import (
    configure_mongoengine, get_config
)
from functools import partial

from marvinbot.models import User
from marvinbot.plugins import load_plugins
import os


lm = LoginManager()
lm.session_protection = "strong"


@lm.user_loader
def load_user(username):
    return User.by_username(username)


def create_before_request(app):
    def before_request():
        g.user = current_user
    return before_request


def make_session_permanent(app, session_timeout=timedelta(days=31)):
    session.permanent = True
    app.permanent_session_lifetime = session_timeout


@lm.unauthorized_handler
def unauthorized():
    if not request.is_xhr:
        return redirect(url_for('marvinbot.login'))
    return jsonify({}), 403


def create_app():
    app = Flask(__name__)

    lm.init_app(app)
    config = get_config()
    web_config = config.get('web_config', {})
    app.secret_key = web_config.get('secret_key')
    app.default_timezone = config.get('default_timezone')

    configure_mongoengine(config)
    configure_logging(config)

    from marvinbot.views import marvinbot

    app.register_blueprint(marvinbot)
    load_plugins(config, None, webapp=app)

    # Add the before request handler
    app.before_request(create_before_request(app))

    if web_config.get('use_permanent_sessions'):
        session_lifetime_seconds = web_config.get('session_timeout_seconds')
        app.before_request(partial(make_session_permanent, app,
                                   session_timeout=timedelta(seconds=session_lifetime_seconds)))

    return app


if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    app = create_app()
    app.run(host='0.0.0.0', debug=True, port=8000)
