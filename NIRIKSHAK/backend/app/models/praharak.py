import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ExternalSignal(Base):
    __tablename__ = "external_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_identifier: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    source_asn: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_service: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    command_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    raw_envelope: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    signature_algorithm: Mapped[str] = mapped_column(String(50), default="NONE", nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False, index=True)
    disposition: Mapped[str] = mapped_column(String(30), default="ALLOWED", nullable=False, index=True)
    factors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    audit_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    incidents: Mapped[list["CrossDomainIncident"]] = relationship("CrossDomainIncident", back_populates="external_signal")


class CircuitBreakerState(Base):
    __tablename__ = "circuit_breaker_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_identifier: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(20), default="CLOSED", nullable=False, index=True)  # CLOSED, HALF-OPEN, OPEN
    request_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    trip_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class CrossDomainIncident(Base):
    __tablename__ = "cross_domain_incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_identifier: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    external_signal_id: Mapped[str] = mapped_column(String(36), ForeignKey("external_signals.id"), nullable=False, index=True)
    internal_event_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("access_events.id"), nullable=True, index=True)
    case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("security_cases.id"), nullable=True, index=True)
    unified_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    attack_pattern: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    external_signal: Mapped["ExternalSignal"] = relationship("ExternalSignal", back_populates="incidents")
    internal_event: Mapped["AccessEvent"] = relationship("AccessEvent")
    case: Mapped["SecurityCase"] = relationship("SecurityCase")
