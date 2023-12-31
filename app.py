import os
from typing import Any

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app() -> Flask:
    basedir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(__name__)
    app.secret_key = 'super secret key'

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(
        basedir, 'db.sqlite3'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from routes import auth, home

    app.register_blueprint(auth.bp)
    app.register_blueprint(home.bp)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from models import User, init_db

    @login_manager.user_loader
    def load_user(user_id: Any) -> User:
        return User.query.get(int(user_id))

    init_db(app)

    return app


if __name__ == '__main__':
    create_app().run()
