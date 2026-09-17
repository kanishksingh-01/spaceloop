import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ResourceClassification(Base):
    __tablename__ = "resource_classifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    level: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    base_sensitivity_score: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    resources: Mapped[list["Resource"]] = relationship("Resource", back_populates="classification")


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    classification_id: Mapped[str] = mapped_column(String(36), ForeignKey("resource_classifications.id"), nullable=False)
    owner_department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    classification: Mapped["ResourceClassification"] = relationship("ResourceClassification", back_populates="resources")
