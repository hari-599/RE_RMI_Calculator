from app import db, app, User
from sqlalchemy import inspect

with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    print("✅ Tables created successfully")
    print("📋 Existing tables:", inspector.get_table_names())
