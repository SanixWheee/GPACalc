import io
import json
import statistics
import zipfile
from collections import defaultdict
from typing import Any, List, Sequence

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app import db
from models import Class, TutorialStatus, User

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def calculate_gpa(classes: Sequence[Class], *, weighted: bool) -> float:
    """
    A method to calculate the GPA of a list of classes

    Parameters
    ----------
    classes: Sequence[Class]
    weighted: bool

    Returns
    -------
    float
    """
    data = []
    weights = []  # a class with 2 credits is worth twice as much with a class with 1
    # the weights account for this problem
    for cls in classes:
        data.append(cls.get_gpa(weighted=weighted))
        weights.append(cls.credits)

    return statistics.harmonic_mean(data=data, weights=weights)


def dot_dot_dot(s: str, max_length: int) -> str:
    """
    A method to shorten a string to a certain length and add '...' to the end

    Parameters
    ----------
    s: str
    max_length: int

    Returns
    -------
    str
    """
    if len(s) > max_length:
        return s[: max_length - 3] + "..."
    return s


def create_pdf(classes: List[Class], user: User) -> None:
    """
    A method to create a report pdf from a list of classes and a username

    Parameters
    ----------
    classes: List[Class]
    user: User
    """
    # sort the classes by grade taken and then alphabetical
    classes.sort(key=lambda c: (c.grade_taken, c.name))

    doc = SimpleDocTemplate(
        f'{current_app.config["REPORT_DIR"]}/{user.get_report_filename()}',
        pagesize=LETTER,
    )
    styles = getSampleStyleSheet()

    heading_style = styles["Heading1"]
    heading_style.alignment = 1
    heading = Paragraph(f"{user.username}'s GPA Report", heading_style)

    # Populate a table with following columns
    # Grade Taken, Name, Received Grade, Credits, Unweighted GPA, Weighted GPA
    data = [
        (
            "Grade Taken",
            "Name",
            "Received Grade",
            "Credits",
            "Unweighted GPA",
            "Weighted GPA",
        )
    ] + [
        (
            str(cls.grade_taken),
            dot_dot_dot(cls.full_name(), 30),
            cls.received_grade,
            str(cls.credits),
            cls.get_gpa(weighted=False),
            cls.get_gpa(weighted=True),
        )
        for cls in classes
    ]

    table = Table(
        data, colWidths=[70, 160, 90, 45, 90, 90]
    )  # the name column needs extra room
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]
    )
    table.setStyle(style)

    # can't calculate GPA if they have no classes added
    if classes:
        unweighted_gpa = calculate_gpa(classes, weighted=False)
        weighted_gpa = calculate_gpa(classes, weighted=True)
    else:
        unweighted_gpa = "Add classes first"
        weighted_gpa = "Add classes first"

    unweighted_gpa_paragraph_style = styles["Heading2"]
    unweighted_gpa_paragraph_style.alignment = 1
    unweighted_gpa_paragraph = Paragraph(
        f"Unweighted GPA: {unweighted_gpa:.2f}", unweighted_gpa_paragraph_style
    )

    weighted_gpa_paragraph_style = styles["Heading2"]
    weighted_gpa_paragraph_style.alignment = 1
    weighted_gpa_paragraph = Paragraph(
        f"Weighted GPA: {weighted_gpa:.2f}", weighted_gpa_paragraph_style
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


with open("all_classes.txt", "r") as f:
    ALL_CLASSES: List[str] = f.read().split("\n")


@bp.route("/", methods=("GET", "POST"))
@login_required
def dashboard() -> Any:
    """
    This is the page where a user can add their classes and calculate their GPA

    Methods
    -------
    GET /dashboard:
        Render the template for dashboard.html
    POST /dashboard:
        Add a class to the user's classes

        Form Data:
            name: str
            type: str
            grade_taken: int
            received_grade: str
            credits: float
    """
    if request.method == "POST":
        name = request.form["name"]
        type = request.form["type"]
        grade_taken = int(request.form["grade_taken"])
        received_grade = request.form["received_grade"]
        try:
            credits = float(request.form["credits"])
        except ValueError:
            flash("Invalid credits value", "error")
        else:
            if credits <= 0:
                flash("Credits must be greater than 0", "error")
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

        return redirect(url_for("dashboard.dashboard"))

    classes = Class.query.filter_by(user_id=current_user.id).all()

    # only pass in the gpa and create a pdf if the user actually has classes
    gpa_kwargs = {"has_classes": False}
    if classes:
        create_pdf(classes, current_user)

        # convert the GPA to 2 decimals
        gpa_kwargs = {
            "unweighted_gpa": f"{calculate_gpa(classes, weighted=False):.2f}",
            "weighted_gpa": f"{calculate_gpa(classes, weighted=True):.2f}",
            "has_classes": True,
        }

    sorted_classes = defaultdict(list)

    for cls in classes:
        sorted_classes[cls.grade_taken].append(cls)

    return render_template(
        "dashboard.html",
        classes_by_grade=sorted_classes,
        all_classes=ALL_CLASSES,
        tutorial_status=current_user.tutorial_status,
        TutorialStatus=TutorialStatus,
        **gpa_kwargs,
    )


@bp.route("/delete_class/<class_id>", methods=("GET",))
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

    return redirect(url_for("dashboard.dashboard"))


@bp.route("/download", methods=("GET",))
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
        current_app.config["REPORT_DIR"],
        current_user.get_report_filename(),
        as_attachment=True,
    )


@bp.route("/update_tutorial_status", methods=("GET",))
@login_required
def update_tutorial_status() -> Any:
    """
    Update the tutorial status of a user

    Methods
    -------
    GET dashboard/update_tutorial_status:
        Update the tutorial status of a user
    """
    current_user.tutorial_status = TutorialStatus(
        current_user.tutorial_status.value + 1
    )
    db.session.add(current_user)
    db.session.commit()
    return "", 204


@bp.route("get_backup_data", methods=("GET",))
@login_required
def get_backup_data() -> Any:
    """
    Get the backup data as a zip file

    Methods
    -------
    GET dashboard/get_backup_data:
        Get the backup data as a zip file
    """
    classes = Class.query.filter_by(user_id=current_user.id).all()
    data = [cls.to_json() for cls in classes]

    data_bytes = json.dumps(data).encode()
    file = io.BytesIO()
    with zipfile.ZipFile(file, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("data.json", data_bytes)

    file.seek(0)
    return send_file(file, as_attachment=True, download_name="backup.zip")


@bp.route("restore_backup_data", methods=("POST",))
@login_required
def restore_backup_data() -> Any:
    """
    Restore the backup data from a zip file

    Methods
    -------
    POST dashboard/restore_backup_data:
        Restore the backup data from a zip file
    """
    file = request.files["file"]
    file_bytes = io.BytesIO(file.read())

    with zipfile.ZipFile(file_bytes, "r") as z:
        with z.open("data.json") as f:
            data_bytes = f.read()

    json_string = data_bytes.decode()
    data = json.loads(json_string)
    classes = Class.query.filter_by(user_id=current_user.id).all()
    class_ids = {cls.id for cls in classes}

    for cls in data:
        # make sure that we are not uploading duplicate classes
        if cls["id"] in class_ids:
            continue

        new_cls = Class(
            id=cls["id"],
            user_id=current_user.id,
            name=cls["name"],
            type=cls["type"],
            grade_taken=cls["grade_taken"],
            received_grade=cls["received_grade"],
            credits=cls["credits"],
        )
        db.session.add(new_cls)
        class_ids.add(cls["id"])

    db.session.commit()
    return redirect(url_for("dashboard.dashboard"))
