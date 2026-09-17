import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.policy import RiskPolicy
from app.models.audit import AuditLog
from app.services.policy_service import PolicyService, DEFAULT_WEIGHTS, DEFAULT_THRESHOLDS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policies", tags=["Policy Management & Dynamic Configuration"])
security_scheme = HTTPBearer(auto_error=False)


class PolicyUpdatePayload(BaseModel):
    value: float = Field(..., description="The new numeric value for the policy")
    justification: Optional[str] = Field(default="Administrative policy adjustment", description="Audit rationale")


class PolicyResponseItem(BaseModel):
    key: str
    category: str
    value: float
    description: Optional[str]
    updated_at: datetime
    updated_by: str


@router.get("", response_model=Dict[str, Any])
async def get_all_policies(db: AsyncSession = Depends(get_db)):
    """Retrieves all active risk scoring weights and decision thresholds."""
    result = await db.execute(select(RiskPolicy))
    policies = result.scalars().all()
    
    current_map = {**DEFAULT_WEIGHTS, **DEFAULT_THRESHOLDS}
    items: List[Dict[str, Any]] = []
    
    for p in policies:
        current_map[p.key] = p.value
        items.append({
            "key": p.key,
            "category": p.category,
            "value": p.value,
            "description": p.description,
            "updated_at": p.updated_at.isoformat(),
            "updated_by": p.updated_by,
        })
        
    # Check weight sum
    weight_keys = ["WEIGHT_IDENTITY", "WEIGHT_DEVICE", "WEIGHT_SENSITIVITY", "WEIGHT_BEHAVIOR", "WEIGHT_ANOMALY", "WEIGHT_CORRELATION"]
    weight_sum = sum(current_map.get(k, 0.0) for k in weight_keys)

    return {
        "policies": items,
        "active_weights": {k: current_map.get(k, 0.0) for k in weight_keys},
        "active_thresholds": {k: current_map.get(k, 0.0) for k in DEFAULT_THRESHOLDS.keys()},
        "weight_sum": round(weight_sum, 3),
        "is_weight_sum_valid": abs(weight_sum - 1.0) < 0.01,
    }


@router.put("/{key}", response_model=PolicyResponseItem)
async def update_policy(
    key: str,
    payload: PolicyUpdatePayload,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Updates a specific policy setting (weight or threshold) with mandatory audit logging."""
    key = key.upper().strip()
    
    import re
    if not re.match(r"^[A-Z0-9_]{3,40}$", key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid policy key format '{key}'. Key must only contain alphanumeric characters and underscores.",
        )

    # Validation
    if key.startswith("WEIGHT_"):
        if not (0.0 <= payload.value <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Weight values must be between 0.0 and 1.0. Received {payload.value}",
            )
    elif key.startswith("THRESHOLD_"):
        if not (0.0 <= payload.value <= 100.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Threshold values must be between 0.0 and 100.0. Received {payload.value}",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported policy key '{key}'. Must start with WEIGHT_ or THRESHOLD_.",
        )

    # Resolve actor
    actor_username = "admin_vikram"
    if credentials:
        token_payload = decode_access_token(credentials.credentials)
        if token_payload:
            actor_username = token_payload.get("sub", "admin_vikram")

    policy = await PolicyService.update_policy(db, key, payload.value, actor_username)

    # Create immutable audit log
    audit_entry = AuditLog(
        id=str(uuid.uuid4()),
        action="policy:update",
        actor_id=None,
        actor_username=actor_username,
        target_entity="risk_policies",
        target_id=key,
        justification=payload.justification or "Policy weight or threshold update",
        details={
            "key": key,
            "new_value": payload.value,
        },
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit_entry)
    await db.commit()

    return PolicyResponseItem(
        key=policy.key,
        category=policy.category,
        value=policy.value,
        description=policy.description,
        updated_at=policy.updated_at,
        updated_by=policy.updated_by,
    )
