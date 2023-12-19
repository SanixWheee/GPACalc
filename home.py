from typing import Any

from flask import Blueprint, render_template, session, redirect, url_for



bp = Blueprint('home', __name__)


@bp.route('/', methods=('GET', 'POST'))
def home() -> Any:
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')
