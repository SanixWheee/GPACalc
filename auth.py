import sqlite3
import functools
from typing import Any, Callable, ParamSpec

from flask import Blueprint, flash, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db


P = ParamSpec('P')


bp = Blueprint('auth', __name__)


def init_db() -> None:
    db = get_db()
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
        '''
    )


@bp.route('/signup', methods=('GET', 'POST'))
def signup() -> Any:
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()

        try:
            db.execute(
                '''
                INSERT INTO users VALUES (?, ?)
                ''',
                (username, generate_password_hash(password))
            )
        except sqlite3.IntegrityError:
            error = 'Username already exists'
        else:
            return redirect(url_for('auth.login'))

    return render_template('signup.html', error=error)


@bp.route('/login', methods=('GET', 'POST'))
def login() -> Any:
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute(
            '''
            SELECT * FROM users WHERE username = ?
            ''',
            (username,)
        ).fetchone()

        if user is None or not check_password_hash(user['password'], password):
            error = 'Incorrect username or password'
        else:
            session.clear()
            session['username'] = username

            flash('Successfully logged in')
            return redirect(url_for('dashboard'))

    return render_template('login.html', error=error)


@bp.route('/logout')
def logout() -> Any:
    session.clear()
    return redirect(url_for('home'))


def login_required(view: Callable[P, Any]) -> Callable[P, Any]:
    @functools.wraps(view)
    def wrapped_view(*args: P.args, **kwargs: P.kwargs):
        if session['username'] is None:
            return redirect(url_for('auth.login'))

        return view(*args, **kwargs)

    return wrapped_view
