import logging
from flask import (
    request, session, g, redirect, url_for, abort, render_template,
    flash, current_app, Blueprint
)
from flask_login import login_user, logout_user, current_user, login_required
from requests_oauthlib import OAuth2Session

from marvinbot.models import User, OAuthClientConfig
from marvinbot.forms import LoginForm
from marvinbot.utils.net import is_safe_url

log = logging.getLogger(__name__)
marvinbot = Blueprint('marvinbot', __name__, template_folder='templates')


@marvinbot.route('/')
@login_required
def home():
    return render_template('index.html')


@marvinbot.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.by_username(form.username.data)

        if user and user.check_password(form.passwd.data):
            login_user(user, remember=True)

            flash('Successful login')

            next_url = request.args.get('next')
            # is_safe_url should check if the url is safe for redirects.
            # See http://flask.pocoo.org/snippets/62/ for an example.
            if not is_safe_url(request, next_url):
                return abort(400)
            return redirect(next_url or url_for(".home"))

    return render_template("login.html", form=form)


@marvinbot.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('.login'))


@marvinbot.route('/oauth2/<plugin_name>/<client_name>/authorize')
@login_required
def oauth_authorize(plugin_name: str, client_name: str):
    client_config = OAuthClientConfig.by_name(plugin_name, client_name)
    if not client_config:
        return abort(404)

    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.
    """
    scopes = request.data.get('scope') or client_config.default_scopes
    if isinstance(scopes, str):
        scopes = scopes.split(',')
    client = OAuth2Session(client_config.client_id, redirect_uri=url_for('.oauth_callback', _external=True),
                           scope=scopes)
    authorization_url, state = client.authorization_url(client_config.authorization_url)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)


@marvinbot.route('/oauth2/<plugin_name>/<client_name>/callback')
@login_required
def oauth_callback(plugin_name: str, client_name: str):
    client_config = OAuthClientConfig.by_name(plugin_name, client_name)
    if not client_config:
        return abort(404)

    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    client = OAuth2Session(client_config.client_id, state=session['oauth_state'],
                           redirect_uri=url_for('.pandadoc_callback', _external=True))
    token = client.fetch_token(client_config.token_url, client_secret=client_config.client_secret,
                               authorization_response=request.url)

    # Store the token
    user = g.user
    user.store_token(client_config, token)
    user.save()

    return redirect(url_for('.home'))

