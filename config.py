from datetime import timedelta
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Automatically load environment variables from .env file
load_dotenv(os.path.join(basedir, ".env"))


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
    SESSION_REFRESH_EACH_REQUEST = True

    # Security: CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # Security: Rate Limiting (Relaxed for dev / interactive testing)
    AUTH_LOGIN_RATE_LIMIT = os.environ.get("AUTH_LOGIN_RATE_LIMIT", "120 per minute")
    AUTH_REGISTER_RATE_LIMIT = os.environ.get("AUTH_REGISTER_RATE_LIMIT", "120 per minute")
    AUTH_PASSWORD_RESET_RATE_LIMIT = os.environ.get("AUTH_PASSWORD_RESET_RATE_LIMIT", "60 per minute")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "300 per minute"

    # Token Expiration Settings (in seconds)
    PASSWORD_RESET_TOKEN_EXPIRY = int(os.environ.get("PASSWORD_RESET_TOKEN_EXPIRY", "3600"))
    EMAIL_VERIFICATION_TOKEN_EXPIRY = int(os.environ.get("EMAIL_VERIFICATION_TOKEN_EXPIRY", "86400"))

    # Security: Limit maximum request size to 5MB to prevent memory DoS
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # AI Service Keys & Models
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    GROQ_FALLBACK_MODEL = os.environ.get("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
    AI_RATE_LIMIT = os.environ.get("AI_RATE_LIMIT", "200 per minute")
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000"
    ).split(",")

    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, "static", "uploads")
