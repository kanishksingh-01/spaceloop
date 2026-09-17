import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_identifier: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    owner_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trust_level: Mapped[str] = mapped_column(String(20), default="UNKNOWN", nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)

    owner: Mapped["User"] = relationship("User")
