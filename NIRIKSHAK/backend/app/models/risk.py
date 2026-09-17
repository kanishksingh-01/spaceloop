import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("access_events.id"), unique=True, nullable=False, index=True)
    total_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # LOW, MODERATE, HIGH, CRITICAL
    identity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    device_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sensitivity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    behavior_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    correlation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event: Mapped["AccessEvent"] = relationship("AccessEvent", back_populates="risk_score")
    factors: Mapped[list["RiskFactor"]] = relationship("RiskFactor", back_populates="risk_score", cascade="all, delete-orphan")


class RiskFactor(Base):
    __tablename__ = "risk_factors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    risk_score_id: Mapped[str] = mapped_column(String(36), ForeignKey("risk_scores.id", ondelete="CASCADE"), nullable=False, index=True)
    factor: Mapped[str] = mapped_column(String(100), nullable=False)
    subscore: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.25)
    contribution: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    explanation: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    risk_score: Mapped["RiskScore"] = relationship("RiskScore", back_populates="factors")
