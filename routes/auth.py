import re
from typing import Any, Optional

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app import db
from models import User

bp = Blueprint('auth', __name__)


def validate_username_and_password(username: str, password: str) -> Optional[str]:
    """
    Validate a username and password

    Parameters
    ----------
    username: str
    password: str

    Returns
    -------
    Optional[str]: a string containing the error or None depending on the result
    """
    if len(username) < 4:
        return 'Username is too short'
    elif User.query.filter_by(username=username).first() is not None:
        return 'Username already taken'
    if len(password) < 8:
        return 'Password must be at least 8 characters'
    elif re.search('[0-9]', password) is None:
        return 'Password must have a number'
    elif re.search('[A-Z]', password) is None:
        return 'Password must have an uppercase letter'
    # None is implicitly returned


@bp.route('/register', methods=('GET', 'POST'))
def register() -> Any:
    """
    Register a new user

    Methods
    -------
    GET /register:
        This is the page a user would see, the html page of register.html is rendered
    POST /register:
        This is called by the frontend and either re-renders the page with an error
        or it redirects the user to the login page while saving their data

        Form Data:
            username: str
            password: str
    """
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # set the error from the username or password validation, or None if no problems
        # if there was no error, then continue
        error = validate_username_and_password(username, password)
        if error is None:
            if User.query.filter_by(username=username).scalar():
                error = 'Username already taken'
            else:
                user = User(username=username)
                user.set_password(password)

                db.session.add(user)
                db.session.commit()

                flash('Account successfully created', 'info')
                return redirect(url_for('auth.login'))

    if error:
        flash(error, 'error')

    return render_template('register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login() -> Any:
    """
    Login a user

    Methods
    -------
    GET /login:
        This is the page a user would see, the html page of login.html is rendered
    POST /Login:
        This is called by the frontend and either re-renders the page with an error
        or it redirects the user to the dashboard and saves the user into the session

        Form Data:
            username: str
            password: str
    """

    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            error = 'Incorrect username or password'
        else:
            login_user(user)
            flash('Successfully logged in', 'info')
            return redirect(url_for('dashboard.dashboard'))

    if error:
        flash(error, 'error')

    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout() -> Any:
    """
    Logout a user

    Methods
    -------
    GET /logout:
        logout the user and redirect them to the main page
    """

    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home.home'))
