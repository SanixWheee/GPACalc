import os
from typing import Any

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_report_dir(app: Flask) -> None:
    if not os.path.exists('/reports'):
        os.mkdir('/reports')

    app.config['REPORT_DIR'] = '/reports'


def create_app() -> Flask:
    basedir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(__name__)
    app.secret_key = 'uper secret key'

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(
        basedir, 'db.sqlite3'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # saves memory
    init_report_dir(app)

    # initialize the blueprints (sections of the website)
    from routes import auth, dashboard, home

    app.register_blueprint(auth.bp)
    app.register_blueprint(home.bp)
    app.register_blueprint(dashboard.bp)

    # initialize the login handler
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from models import User, init_db

    @login_manager.user_loader
    def load_user(user_id: Any) -> User:
        """A custom user loader to use the User model"""
        return User.query.get(int(user_id))

    init_db(app)

    return app


if __name__ == '__main__':
    create_app().run()
