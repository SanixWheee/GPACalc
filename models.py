from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from logger import get_logger

if TYPE_CHECKING:
    from flask import Flask


log = get_logger(__name__)


letter_to_gpa: Dict[str, float] = {
    "A": 4.0,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "N": 0.0,
}


class User(UserMixin, db.Model):
    """
    A model to represent a user

    Attributes
    ----------
    id: int
    username: str
    password: str
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    has_completed_tutorial = db.Column(db.Boolean, nullable=False)

    def set_password(self, password: str) -> None:
        """
        Set a password for the user in a secure manner

        Parameters
        ----------
        password: str
        """
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Check a password for the user by auto-converting it to the secure form

        Parameters
        ----------
        password: str

        Returns
        -------
        :class:`bool` representing whether the password parameter matches the attribute
        """
        return check_password_hash(self.password, password)

    def get_report_filename(self) -> str:
        """
        Get the filename for the report of the user
        """
        return f"{self.username}_report.pdf"


class Class(db.Model):
    """
    A model to represent a class taken

    Attributes
    ----------
    id: int
    user_id: int
    name: str
    type: str
    grade_taken: int
    received_grade: str
    credits: float
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    grade_taken = db.Column(db.Integer, nullable=False)
    received_grade = db.Column(db.String, nullable=False)
    credits = db.Column(db.Float, nullable=False)

    def full_name(self) -> str:
        """
        Get the full name of the class
        """
        return f"{self.type} {self.name}".strip()

    def get_gpa(self, *, weighted: bool) -> float:
        """
        Get the GPA of the user

        Parameters
        ----------
        weighted: bool

        Returns
        -------
        float
        """
        gpa = letter_to_gpa[self.received_grade]
        if weighted:
            if self.type == "AP":
                gpa += 1.0
            elif self.type == "Honors":
                gpa += 0.5
        return gpa


def init_db(app: Flask) -> None:
    # by putting this function in the models.py file,
    # it is ensured that all models have been loaded
    # because then this function is imported
    # all models above also are
    log.info("Creating database tables...")
    db.init_app(app)
    with app.app_context():
        db.create_all()
    log.info("Database tables created")
