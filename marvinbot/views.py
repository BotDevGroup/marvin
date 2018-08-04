import logging
from flask import (
    request, session, g, redirect, url_for, abort, render_template,
    flash, current_app, Blueprint
)
from flask_login import login_user, logout_user, current_user, login_required
from marvinbot.models import User
from marvinbot.forms import LoginForm, ChangePasswordForm
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
        else:
            flash('Invalid credentials', 'error')

    return render_template("login.html", form=form)


@marvinbot.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('.login'))


@marvinbot.route('/authentication/change_password', methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        user = g.user

        if user.check_password(form.old_password.data):
            user.change_password(form.new_password.data)
            flash('Password changed successfully')

            return redirect(url_for(".home"))
    return render_template('auth/change_password.html', form=form)

