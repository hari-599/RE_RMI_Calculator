from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from routes import app_routes
from models import db, User
from extensions import mail
from slugify import slugify
import os
import redis
from dotenv import load_dotenv

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
# Register slugify as a Jinja global
app.jinja_env.globals.update(slugify=slugify)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('USER_MAIL'),
    MAIL_PASSWORD=os.getenv('USER_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.getenv('USER_MAIL'),
)

mail.init_app(app)
# Register routes from routes.py
app.register_blueprint(app_routes)
with app.app_context():
    db.create_all()
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)