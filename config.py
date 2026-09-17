from datetime import timedelta
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Use environment secret key; in production this must be kept confidential
    SECRET_KEY = os.environ.get("SECRET_KEY", "spaceloop-dev-secret-key-change-in-prod-2026")
    
    _raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "app.db"))
    if _raw_db_url.startswith("postgres://"):
        _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security: Cookie & Session hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Security: Limit maximum request size to 5MB to prevent memory DoS
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # AI Service Keys
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")
