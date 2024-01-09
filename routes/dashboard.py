from typing import Any, Sequence

from flask import Blueprint, render_template
from flask_login import current_user

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen.canvas import Canvas

from models import Class

bp = Blueprint('dashboard', __name__)


def create_pdf(classes: Sequence[Class]) -> None:
    ...


@bp.route('/dashboard', methods=('GET',))
def dashboard() -> Any:
    classes = Class.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', classes=classes)
