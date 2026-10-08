"""
SpaceLoop Fraud Engine Database Session & Repository Layer
Reuses existing database models (User, Space, Booking, FraudEventRecord, FraudAlertRecord).
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import Config
from models import db, User, Space, Booking, DeviceSession, FraudEventRecord, FraudAlertRecord

# Configure SQLAlchemy engine using the project's canonical DB URI
try:
    engine = create_engine(
        Config.SQLALCHEMY_DATABASE_URI,
        connect_args={"check_same_thread": False} if "sqlite" in Config.SQLALCHEMY_DATABASE_URI else {}
    )
except Exception:
    # If the configured URI failed (e.g. driver mismatch), try fallback drivers or local SQLite
    _fallback_uri = Config.SQLALCHEMY_DATABASE_URI
    if "postgresql" in _fallback_uri and "+psycopg2" not in _fallback_uri:
        _fallback_uri = _fallback_uri.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        _fallback_uri = "sqlite:///app.db"
    engine = create_engine(
        _fallback_uri,
        connect_args={"check_same_thread": False} if "sqlite" in _fallback_uri else {}
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for thread-safe database sessions."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


from sqlalchemy import inspect, text
from models import db, User, Space, Booking, DeviceSession, FraudEventRecord, FraudAlertRecord, RiskAssessment


def ensure_fraud_tables():
    """Ensures device_sessions, risk_assessments, fraud_events and fraud_alerts tables exist."""
    try:
        DeviceSession.__table__.create(bind=engine, checkfirst=True)
        RiskAssessment.__table__.create(bind=engine, checkfirst=True)
        FraudEventRecord.__table__.create(bind=engine, checkfirst=True)
        FraudAlertRecord.__table__.create(bind=engine, checkfirst=True)

        inspector = inspect(engine)
        if "spaces" in inspector.get_table_names():
            space_cols = {col["name"] for col in inspector.get_columns("spaces")}
            if "embedding_json" not in space_cols:
                with engine.connect() as conn:
                    col_type = "JSON" if "postgres" in str(engine.url).lower() else "TEXT"
                    conn.execute(text(f"ALTER TABLE spaces ADD COLUMN embedding_json {col_type}"))
                    conn.commit()
    except Exception:
        pass


# Ensure tables are present on module load
ensure_fraud_tables()
