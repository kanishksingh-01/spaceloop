from app import create_app
from models import db, User
app = create_app()
with app.app_context():
    admin = User.query.filter_by(email="admin@spaceloop.in").first()
    if not admin:
        admin = User(name="SpaceLoop Admin", email="admin@spaceloop.in", role="admin")
        admin.set_password("AdminPass123!")
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@spaceloop.in (Password: AdminPass123!)")
    else:
        print("Admin already exists.")
