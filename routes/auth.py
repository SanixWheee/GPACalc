from typing import Any

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app import db
from models import User

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=("GET", "POST"))
def register() -> Any:
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first() is not None:
            error = "Username already taken"
        else:
            user = User(username=username)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash("Account successfully created")
            return redirect(url_for("auth.login"))

    return render_template("register.html", error=error)


@bp.route("/login", methods=("GET", "POST"))
def login() -> Any:
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            error = "Incorrect username or password"
        else:
            login_user(user)
            flash("Successfully logged in")
            return redirect(url_for("dashboard"))

    return render_template("login.html", error=error)


@bp.route("/logout")
@login_required
def logout() -> Any:
    logout_user()
    flash("You have been logged out")
    return redirect(url_for("home"))
