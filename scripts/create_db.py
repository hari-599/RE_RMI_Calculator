from sqlalchemy import inspect

from app import app
from re_rmi.models import db

with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    print("✅ Tables created successfully")
    print("📋 Existing tables:", inspector.get_table_names())
