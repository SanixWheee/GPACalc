import statistics
from typing import Any, Dict, List, Sequence, Tuple

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app import db
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


def get_statistical_data(classes: Sequence[Class]) -> Tuple[List[float], List[float]]:
    """
    Get the data to pass into statistics.harmonic_mean(), this includes the actual data
    and the data's weightages
    """
    data = []
    weights = []  # a class with 2 credits is worth twice as much with a class with 1
    # the weights account for this problem
    for cls in classes:
        data.append(letter_to_gpa[cls.received_grade])
        weights.append(cls.credits)

    return data, weights


def calculate_unweighted_gpa(classes: Sequence[Class]) -> float:
    """Calculate unweighted GPA for a sequence of classes"""
    return statistics.harmonic_mean(*get_statistical_data(classes))


def get_weighted_gpa_bonus(cls: Class) -> float:
    """Returns the bonus a class gets for a weighted GPA"""
    if cls.type == 'AP':
        return 1.0
    elif cls.type == 'Honors':
        return 0.5
    return 0.0


def calculate_weighted_gpa(classes: Sequence[Class]) -> float:
    data, weights = get_statistical_data(classes)

    # classes is an ordered list so we can just go through the data and add the bonus
    for i, cls in enumerate(classes):
        data[i] += get_weighted_gpa_bonus(cls)

    return statistics.harmonic_mean(data=data, weights=weights)


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
    doc = SimpleDocTemplate(
        f'{current_app.config["REPORT_DIR"]}/{user.get_report_filepath()}',
        pagesize=LETTER,
    )
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
            f'{cls.type} {cls.name}'.strip(),  # no honors or AP leaves an empty space at the start
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

    # can't calculate GPA if they have no classes added
    if classes:
        unweighted_gpa = calculate_unweighted_gpa(classes)
        weighted_gpa = calculate_weighted_gpa(classes)
    else:
        unweighted_gpa = 'Add classes first'
        weighted_gpa = 'Add classes first'

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


@bp.route('/dashboard', methods=('GET', 'POST'))
@login_required
def dashboard() -> Any:
    """
    This is the page where a user can add their classes and calculate their GPA

    Methods
    -------
    GET /dashboard:
        Render the template for dashboard.html
    """
    if request.method == 'POST':
        name = request.form['name']
        type = request.form['type']
        grade_taken = int(request.form['grade_taken'])
        received_grade = request.form['received_grade']
        try:
            credits = float(request.form['credits'])
        except ValueError:
            flash('Invalid credits value', 'error')
        else:
            cls = Class(
                user_id=current_user.id,
                name=name,
                type=type,
                grade_taken=grade_taken,
                received_grade=received_grade,
                credits=credits,
            )
            db.session.add(cls)
            db.session.commit()

    classes = Class.query.filter_by(user_id=current_user.id).all()

    # only pass in the gpa and create a pdf if the user actually has classes
    gpa_kwargs = {'has_classes': False}
    if classes:
        create_pdf(classes, current_user)

        # convert the GPA to 2 decimals
        gpa_kwargs = {
            'unweighted_gpa': f'{calculate_unweighted_gpa(classes):.2f}',
            'weighted_gpa': f'{calculate_unweighted_gpa(classes):.2f}',
            'has_classes': True,
        }

    # html tables only support creation by row so we must convert our data
    # to fit the table spec
    class_table_rows = [[], [], [], []]
    for cls in classes:
        # 9th grade is index 0, 10th grade is index 1, etc
        class_table_rows[cls.grade_taken - 9].append(cls)

    # fill in extra values at the end with None
    max_length = max(map(len, class_table_rows))
    for grade in class_table_rows:
        grade.extend([None] * (max_length - len(grade)))

    # convert the table from rows to columns
    class_table = []
    for a, b, c, d in zip(
        class_table_rows[0],
        class_table_rows[1],
        class_table_rows[2],
        class_table_rows[2],
    ):
        class_table.append([a, b, c, d])

    return render_template('dashboard.html', classes=class_table, **gpa_kwargs)


@bp.route('/dashboard/download', methods=('GET',))
@login_required
def download_report() -> Any:
    """
    This page downloads the report pdf for a user

    Methods
    -------
    GET dashboard/download:
        Returns the pdf file
    """
    return send_from_directory(
        current_app.config['REPORT_DIR'], current_user.get_report_filepath()
    )


@bp.route('/dashboard/delete_class/<class_id>', methods=('GET',))
def delete_class(class_id: int) -> Any:
    """
    This route deletes a class from a user's classes

    Methods
    -------
    GET dashboard/delete_class/<class_id>:
        Deletes the class
    """
    cls = Class.query.get_or_404(class_id)
    db.session.delete(cls)
    db.session.commit()

    return redirect(url_for('dashboard.dashboard'))
