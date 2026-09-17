import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SecurityCase(Base):
    __tablename__ = "security_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_identifier: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", nullable=False, index=True)  # OPEN, DISMISSED, ESCALATED
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # HIGH, CRITICAL
    primary_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("access_events.id"), nullable=True)
    assigned_analyst_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    primary_user: Mapped["User"] = relationship("User", foreign_keys=[primary_user_id])
    assigned_analyst: Mapped["User"] = relationship("User", foreign_keys=[assigned_analyst_id])
    event: Mapped["AccessEvent"] = relationship("AccessEvent")
