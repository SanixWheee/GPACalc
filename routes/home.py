from typing import Any

from flask import Blueprint, render_template

bp = Blueprint("home", __name__)


@bp.route("/", methods=("GET",))
def home() -> Any:
    """
    This is the main page

    Methods
    -------
    GET /:
        Render the template for index.html
    """
    
    return render_template("index.html")
