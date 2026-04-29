from flask import render_template, redirect, url_for, flash, request
from urllib.parse import urlsplit, urlunsplit
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .forms import LoginForm, RegisterForm
from ..models import db, User


def _safe_redirect_url(target):
    """Return a safe, same-host redirect URL or None.

    Reconstructs the URL using only the path and query components so that
    a crafted host or scheme in the ``next`` parameter cannot redirect the
    user to an external site (open-redirect prevention).
    """
    if not target:
        return None
    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(target)
    # Must be empty netloc (relative) or exactly the same host
    if test_url.netloc and test_url.netloc != ref_url.netloc:
        return None
    # Reconstruct with no scheme/netloc – relative path only
    return urlunsplit(("", "", test_url.path, test_url.query, "")) or None


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            redirect_url = _safe_redirect_url(request.args.get("next")) or url_for("main.index")
            flash("Login realizado com sucesso!", "success")
            return redirect(redirect_url)
        flash("E-mail ou senha inválidos.", "danger")
    return render_template("auth/login.html", form=form)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Cadastro realizado com sucesso! Faça login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("main.index"))
