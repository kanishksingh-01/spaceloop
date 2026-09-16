from models import db
def get_db_session():
    return db.session
