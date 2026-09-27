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
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False} if "sqlite" in Config.SQLALCHEMY_DATABASE_URI else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for thread-safe database sessions."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def ensure_fraud_tables():
    """Ensures device_sessions, risk_assessments, fraud_events and fraud_alerts tables exist."""
    try:
        DeviceSession.__table__.create(bind=engine, checkfirst=True)
        RiskAssessment.__table__.create(bind=engine, checkfirst=True)
        FraudEventRecord.__table__.create(bind=engine, checkfirst=True)
        FraudAlertRecord.__table__.create(bind=engine, checkfirst=True)
    except Exception:
        pass


# Ensure tables are present on module load
ensure_fraud_tables()
