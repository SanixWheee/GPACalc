from __future__ import annotations

from typing import TYPE_CHECKING

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db

if TYPE_CHECKING:
    from flask import Flask


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

    def get_report_filepath(self) -> str:
        return f'{self.username}_report.pdf'


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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    grade_taken = db.Column(db.Integer, nullable=False)
    received_grade = db.Column(db.String, nullable=False)
    credits = db.Column(db.Float, nullable=False)


def init_db(app: Flask) -> None:
    # by putting this function in the models.py file,
    # it is ensured that all models have been loaded
    # because then this function is imported
    # all models above also are
    db.init_app(app)
    with app.app_context():
        db.create_all()
