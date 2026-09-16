from app import create_app
from seed_data import seed_database
app = create_app()
with app.app_context():
    seed_database()
    print("Database seeded with campus micro-spaces and verified users.")
