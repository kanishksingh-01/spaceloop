"""
SpaceLoop Fraud Engine Pydantic Schemas
Normalized event definitions, score requests, alerts, and responses.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FraudEventType(str, Enum):
    ACCOUNT_CREATED = "account_created"
    LOGIN = "login"
    PROFILE_UPDATED = "profile_updated"
    LISTING_CREATED = "listing_created"
    LISTING_UPDATED = "listing_updated"
    BOOKING_CREATED = "booking_created"
    BOOKING_CANCELLED = "booking_cancelled"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_COMPLETED = "payment_completed"
    REFUND_REQUESTED = "refund_requested"
    REFUND_COMPLETED = "refund_completed"
    DEVICE_CHANGED = "device_changed"
    LOCATION_CHANGED = "location_changed"


class FraudDecision(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    CHALLENGE = "challenge"
    HOLD = "hold"
    BLOCK = "block"


class FraudSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudRiskLevel(str, Enum):
    NORMAL = "normal"
    UNUSUAL = "unusual"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"


class GeoLocation(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    city: Optional[str] = None
    country: Optional[str] = "IN"


class FraudEventInput(BaseModel):
    """
    Normalized SpaceLoop Ingestion Event.
    """
    event_id: Optional[str] = None
    event_type: FraudEventType
    timestamp: Optional[datetime] = None
    user_id: Optional[int] = None
    entity_type: str = Field(default="user", description="'user', 'listing', 'booking', 'payment', 'device'")
    entity_id: Optional[int] = None
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[GeoLocation] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None


class ScoreRequest(BaseModel):
    """
    On-demand risk scoring request for prospective transactions or actions.
    """
    event_type: FraudEventType
    user_id: Optional[int] = None
    entity_type: str = "booking"
    entity_id: Optional[int] = None
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    location: Optional[GeoLocation] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class RuleResult(BaseModel):
    code: str
    name: str
    category: str
    severity: FraudSeverity
    weight: float
    triggered: bool
    evidence: str


class FraudScoreResponse(BaseModel):
    risk_score: float
    confidence: float
    risk_level: FraudRiskLevel
    decision: FraudDecision
    triggered_rules: List[RuleResult]
    features: Dict[str, Any]


class EventIngestResponse(BaseModel):
    status: str = "ingested"
    event_id: str
    event_type: FraudEventType
    risk_score: float
    risk_level: FraudRiskLevel
    decision: FraudDecision
    alert_id: Optional[str] = None
    created_at: str


class AlertResponse(BaseModel):
    id: int
    alert_id: str
    event_id: str
    user_id: Optional[int] = None
    entity_type: str
    entity_id: Optional[int] = None
    severity: FraudSeverity
    risk_score: float
    decision: FraudDecision
    status: str
    triggered_rules: List[Dict[str, Any]]
    features_snapshot: Dict[str, Any]
    notes: Optional[str] = ""
    created_at: str
    resolved_at: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "SpaceLoop Fraud Engine"
    version: str = "1.0.0"
    framework: str = "FastAPI + Pandas + NumPy"
    timestamp: str
