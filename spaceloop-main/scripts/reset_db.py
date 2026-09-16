import os
from app import create_app
from models import db
from seed_data import seed_database
app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    seed_database()
    print("Database reset and re-seeded cleanly.")
