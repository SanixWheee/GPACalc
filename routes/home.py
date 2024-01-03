from typing import Any

from flask import Blueprint, redirect, render_template, session, url_for

bp = Blueprint("home", __name__)


@bp.route("/", methods=("GET",))
def home() -> Any:
    return render_template("index.html")
