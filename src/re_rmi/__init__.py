import os
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from slugify import slugify
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "instance" / "database.db"
load_dotenv(PROJECT_ROOT / ".env")

from .extensions import mail  # noqa: E402
from .models import User, db  # noqa: E402
from .routes import app_routes  # noqa: E402


def create_app():
    app = Flask(
        __name__,
        instance_path=str(PROJECT_ROOT / "instance"),
        static_folder="static",
        template_folder="templates",
    )

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "thisisasecretkey"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{DATABASE_PATH.as_posix()}",
        MAIL_SERVER="smtp.gmail.com",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv("USER_MAIL"),
        MAIL_PASSWORD=os.getenv("USER_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv("USER_MAIL"),
    )

    app.jinja_env.globals.update(slugify=slugify)

    db.init_app(app)
    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(app_routes)

    with app.app_context():
        db.create_all()

    return app
