import uuid
from datetime import datetime, timezone
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AccessEvent(Base):
    __tablename__ = "access_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("resources.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[str] = mapped_column(String(20), default="SUCCESS", nullable=False)
    data_volume: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    source_context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User")
    device: Mapped["Device"] = relationship("Device")
    resource: Mapped["Resource"] = relationship("Resource")
    risk_score: Mapped["RiskScore"] = relationship("RiskScore", back_populates="event", uselist=False)
