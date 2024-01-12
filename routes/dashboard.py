from typing import Any, Dict, List, Sequence

from flask import Blueprint, render_template, send_from_directory, current_app
from flask_login import current_user, login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models import Class, User

bp = Blueprint('dashboard', __name__)

letter_to_gpa: Dict[str, float] = {
    'A': 4.0,
    'B+': 3.3,
    'B': 3.0,
    'B-': 2.7,
    'C+': 2.3,
    'C': 2.0,
    'C-': 1.7,
    'N': 0.0,
}


def calculate_unweighted_gpa(classes: Sequence[Class]) -> float:
    """Calculate unweighted GPA for a sequence of classes"""
    return sum(letter_to_gpa[cls.received_grade] for cls in classes) / len(classes)


def get_weighted_gpa_bonus(cls: Class) -> float:
    """Returns the bonus a class gets for a weighted GPA"""
    if cls.type == 'AP':
        return 1.0
    elif cls.type == 'Honors':
        return 0.5
    return 0.0


def calculate_weighted_gpa(classes: Sequence[Class]) -> float:
    """Calculate weighted GPA for a sequence of classes"""
    return sum(
        letter_to_gpa[cls.received_grade] + get_weighted_gpa_bonus(cls)
        for cls in classes
    ) / len(classes)


def create_pdf(classes: List[Class], user: User) -> None:
    """
    A method to create a report pdf from a list of classes and a username

    Parameters
    ----------
    classes: List[Class]
    username: str
    """
    # sort the classes by grade taken and then alphabetical
    classes.sort(key=lambda c: (c.grade_taken, c.name))

    # the file name is their username + _report.pdf
    doc = SimpleDocTemplate(user.get_report_filepath(), pagesize=LETTER)
    styles = getSampleStyleSheet()

    heading_style = styles['Heading1']
    heading_style.alignment = 1
    heading = Paragraph(f'{user.username}\'s GPA Report', heading_style)

    # Populate a table with following columns
    # Grade Taken, Name, Received Grade, Credits, Unweighted GPA, Weighted GPA
    data = [
        (
            'Grade Taken',
            'Name',
            'Received Grade',
            'Credits',
            'Unweighted GPA',
            'Weighted GPA',
        )
    ] + [
        (
            str(cls.grade_taken),
            f'{cls.type} {cls.name}',
            cls.received_grade,
            str(cls.credits),
            letter_to_gpa[cls.received_grade],
            letter_to_gpa[cls.received_grade] + get_weighted_gpa_bonus(cls),
        )
        for cls in classes
    ]

    # format the table with colors and a specific width
    column_count = len(data[0])

    #                             500 is the target width
    table = Table(data, colWidths=[500 / column_count] * column_count)
    style = TableStyle(
        [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]
    )
    table.setStyle(style)

    unweighted_gpa = calculate_unweighted_gpa(classes)
    weighted_gpa = calculate_weighted_gpa(classes)

    unweighted_gpa_paragraph_style = styles['Heading2']
    unweighted_gpa_paragraph_style.alignment = 1
    unweighted_gpa_paragraph = Paragraph(
        f'Unweighted GPA: {unweighted_gpa:.2f}', unweighted_gpa_paragraph_style
    )

    weighted_gpa_paragraph_style = styles['Heading2']
    weighted_gpa_paragraph_style.alignment = 1
    weighted_gpa_paragraph = Paragraph(
        f'Weighted GPA: {weighted_gpa:.2f}', weighted_gpa_paragraph_style
    )

    doc.build(
        [
            heading,
            Spacer(1, 12),
            table,
            Spacer(1, 12),
            unweighted_gpa_paragraph,
            weighted_gpa_paragraph,
        ]
    )


@bp.route('/dashboard', methods=('GET',))
@login_required
def dashboard() -> Any:
    """
    This is the page where a user can add their classes and calculate their GPA

    Methods
    -------
    GET /dashboard:
        Render the template for dashboard.html
    """

    classes = Class.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', classes=classes)


@bp.route('/dashboard/download', methods=('GET,'))
def download_report() -> Any:
    """
    This page downloads the report pdf for a user

    Methods
    -------
    GET dashboard/download:
        Returns the pdf file
    """
    return send_from_directory(current_app.config['REPORT_DIR'], current_user.get_report_filepath())
