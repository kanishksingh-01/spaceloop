import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    actor_username: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g. "case:escalate", "case:dismiss"
    target_entity: Mapped[str] = mapped_column(String(50), nullable=False)        # e.g. "security_cases"
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)     # case_id
    justification: Mapped[str] = mapped_column(Text, nullable=False)              # Mandatory reason
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
