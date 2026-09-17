import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventCreateRequest(BaseModel):
    event_id: Optional[str] = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:10]}")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_identifier: str = Field(..., description="User UUID or external identifier (e.g. USER-001)")
    device_identifier: str = Field(..., description="Device UUID or hardware identifier (e.g. DEV-101)")
    resource_identifier: str = Field(..., description="Resource UUID or repository name (e.g. Operational Repository A)")
    session_id: Optional[str] = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    action: str = Field(default="READ", description="Operation (READ, WRITE, EXPORT, DELETE)")
    result: str = Field(default="SUCCESS", description="Outcome (SUCCESS, DENIED, CHALLENGED)")
    data_volume: int = Field(default=1048576, description="Data volume transferred in bytes")
    source_context: Dict[str, Any] = Field(default_factory=dict, description="Context (mfa_verified, client_ip, etc.)")


class EventListItem(BaseModel):
    id: str
    event_id: str
    timestamp: datetime
    user_id: str
    user_identifier: str
    department: str
    device_identifier: str
    resource_name: str
    action: str
    result: str
    data_volume: int
    risk_score: float
    risk_level: str
    case_id: Optional[str] = None


class ScenarioTriggerRequest(BaseModel):
    scenario: str = Field(..., description="'normal', 'off_hours', or 'exfiltration'")


class ScenarioTriggerResponse(BaseModel):
    scenario: str
    event_id: str
    internal_id: str
    total_score: float
    risk_level: str
    case_created: bool
    case_id: Optional[str] = None
    summary: str
