from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.risk import FactorDetail


class CaseListItem(BaseModel):
    id: str
    case_identifier: str
    status: str
    severity: str
    opened_at: datetime
    primary_user_identifier: str
    department: str
    event_id: Optional[str] = None
    resource_name: Optional[str] = None
    risk_score: Optional[float] = None


class CaseReviewRequest(BaseModel):
    action: str = Field(..., description="Must be 'DISMISS' or 'ESCALATE'")
    justification: str = Field(..., min_length=5, description="Mandatory explanation for review decision")


class CaseReviewResponse(BaseModel):
    case_id: str
    case_identifier: str
    status: str
    reviewed_by: str
    justification: str
    audit_log_id: str
    timestamp: datetime


class CaseDetailResponse(BaseModel):
    id: str
    case_identifier: str
    status: str
    severity: str
    opened_at: datetime
    updated_at: datetime
    primary_user_id: str
    primary_user_identifier: str
    department: str
    assigned_analyst: Optional[str] = None
    event_id: Optional[str] = None
    event_timestamp: Optional[datetime] = None
    resource_name: Optional[str] = None
    device_identifier: Optional[str] = None
    total_score: Optional[float] = None
    risk_level: Optional[str] = None
    factors: List[FactorDetail] = Field(default_factory=list)
    audit_history: List[Dict[str, Any]] = Field(default_factory=list)


class AuditLogItem(BaseModel):
    id: str
    timestamp: datetime
    actor_username: str
    action: str
    target_entity: str
    target_id: Optional[str] = None
    justification: str
    details: Dict[str, Any] = Field(default_factory=dict)
