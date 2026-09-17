from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.risk import FactorDetail


class ExternalSignalCreateRequest(BaseModel):
    signal_identifier: Optional[str] = None
    timestamp: Optional[datetime] = None
    source_ip: str = Field(..., description="IPv4 or IPv6 of the external connection")
    source_asn: Optional[str] = Field(default=None, description="BGP ASN identifier")
    target_service: str = Field(..., description="Target service/API name")
    command_type: str = Field(..., description="Signal/Command type, e.g., TELEMETRY, FIRE_ORDER, DRONE_REROUTE, AUTH")
    raw_envelope: Dict[str, Any] = Field(
        default_factory=dict,
        description="Envelope containing payload, timestamp, nonce, key_id, signature, algorithm"
    )


class ExternalSignalResponse(BaseModel):
    id: str
    signal_identifier: str
    timestamp: datetime
    source_ip: str
    source_asn: Optional[str]
    target_service: str
    command_type: str
    raw_envelope: Dict[str, Any]
    signature_valid: bool
    signature_algorithm: str
    risk_score: float
    risk_tier: str
    disposition: str
    factors: List[FactorDetail]
    audit_hash: str
    created_at: datetime


class CircuitBreakerStatusResponse(BaseModel):
    id: str
    source_identifier: str
    state: str
    request_count: int
    window_start: datetime
    trip_expires_at: Optional[datetime]
    is_quarantined: bool


class CircuitBreakerResetRequest(BaseModel):
    source_identifier: str


class CrossDomainIncidentResponse(BaseModel):
    id: str
    incident_identifier: str
    external_signal_id: str
    internal_event_id: Optional[str]
    case_id: Optional[str]
    unified_risk_score: float
    attack_pattern: str
    summary: str
    detected_at: datetime


class PraharakScenarioTriggerRequest(BaseModel):
    scenario: str = Field(
        ...,
        description="Scenario key: normal_telemetry, spoofed_command, ddos_flood, hybrid_coordinated_attack"
    )


class PraharakScenarioTriggerResponse(BaseModel):
    scenario: str
    signal_identifier: str
    risk_score: float
    risk_tier: str
    disposition: str
    circuit_breaker_tripped: bool
    cross_domain_incident_id: Optional[str] = None
    summary: str
