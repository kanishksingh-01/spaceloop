from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FactorDetail(BaseModel):
    factor: str
    subscore: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    contribution: float = Field(..., ge=0.0, le=100.0)
    explanation: str
    details: Dict[str, Any] = Field(default_factory=dict)


class RiskResult(BaseModel):
    total_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    identity_score: float = Field(..., ge=0.0, le=100.0)
    device_score: float = Field(..., ge=0.0, le=100.0)
    sensitivity_score: float = Field(..., ge=0.0, le=100.0)
    behavior_score: float = Field(..., ge=0.0, le=100.0)
    anomaly_score: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)
    correlation_score: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)
    factors: List[FactorDetail] = Field(default_factory=list)


class EventExplanationResponse(BaseModel):
    event_id: str
    total_score: float
    risk_level: str
    factors: List[FactorDetail]
