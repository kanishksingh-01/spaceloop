import uuid
from datetime import datetime, timezone
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BehaviorBaseline(Base):
    __tablename__ = "behavior_baselines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    typical_hours: Mapped[dict] = mapped_column(JSON, nullable=False, default=lambda: {"start": 9, "end": 18})
    typical_devices: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    typical_resources: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    avg_daily_volume: Mapped[int] = mapped_column(BigInteger, default=15728640, nullable=False)
    std_daily_volume: Mapped[int] = mapped_column(BigInteger, default=5242880, nullable=False)
    baseline_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="baseline")
