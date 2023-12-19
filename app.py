from flask import Flask

import auth
import home
import db


def create_app() -> Flask:
    app = Flask(__name__)

    with app.app_context():
        auth.init_db()

    app.teardown_appcontext(db.close_db)
    app.register_blueprint(home.bp)
    app.register_blueprint(auth.bp)

    return app


if __name__ == '__main__':
    create_app().run()
