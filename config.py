import os

basedir = os.path.abspath(os.path.dirname(__file__))

_db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "app.db"))
# Render's managed Postgres gives a "postgres://" URL; SQLAlchemy 2.x needs "postgresql://".
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cycle-care-secret-key-2026")
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    } if not _db_url.startswith("sqlite") else {}

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
