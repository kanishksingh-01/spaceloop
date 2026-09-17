import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.device import Device
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["Endpoint & Device Posture Management"])
security_scheme = HTTPBearer(auto_error=False)


class DeviceTrustUpdateRequest(BaseModel):
    trust_level: str = Field(..., description="Target trust level: TRUSTED, MONITORED, or REVOKED")
    justification: str = Field(..., min_length=5, description="Mandatory analyst justification")


class DeviceItem(BaseModel):
    id: str
    device_identifier: str
    device_type: str
    registered: bool
    trust_level: str
    owner_username: Optional[str]
    status: str
    first_seen: datetime
    last_seen: datetime


@router.get("", response_model=List[DeviceItem])
async def list_devices(db: AsyncSession = Depends(get_db)):
    """Lists all endpoints, corporate enrollment state, and trust posture."""
    stmt = select(Device).options(selectinload(Device.owner)).order_by(desc(Device.last_seen))
    result = await db.execute(stmt)
    devices = result.scalars().all()

    return [
        DeviceItem(
            id=d.id,
            device_identifier=d.device_identifier,
            device_type=d.device_type,
            registered=d.registered,
            trust_level=d.trust_level,
            owner_username=d.owner.username if d.owner else None,
            status=d.status,
            first_seen=d.first_seen,
            last_seen=d.last_seen,
        )
        for d in devices
    ]


@router.patch("/{device_id}/trust", response_model=DeviceItem)
async def update_device_trust(
    device_id: str,
    payload: DeviceTrustUpdateRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Analyst action to update endpoint trust posture (TRUSTED, MONITORED, REVOKED) with audit logging."""
    target_trust = payload.trust_level.upper().strip()
    if target_trust not in ["TRUSTED", "MONITORED", "REVOKED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trust level. Must be one of: TRUSTED, MONITORED, REVOKED",
        )

    stmt = (
        select(Device)
        .options(selectinload(Device.owner))
        .where((Device.id == device_id) | (Device.device_identifier == device_id))
    )
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found.",
        )

    previous_trust = device.trust_level
    device.trust_level = target_trust
    if target_trust == "REVOKED":
        device.status = "SUSPENDED"
    elif target_trust == "TRUSTED":
        device.status = "ACTIVE"

    # Identify acting analyst
    actor_username = "analyst_sarah"
    if credentials:
        token_payload = decode_access_token(credentials.credentials)
        if token_payload:
            actor_username = token_payload.get("sub", "analyst_sarah")

    # Record immutable audit log
    audit_entry = AuditLog(
        id=str(uuid.uuid4()),
        action="device:update_trust",
        actor_id=None,
        actor_username=actor_username,
        target_entity="devices",
        target_id=device.id,
        justification=payload.justification,
        details={
            "device_identifier": device.device_identifier,
            "previous_trust_level": previous_trust,
            "new_trust_level": target_trust,
        },
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit_entry)
    await db.commit()
    await db.refresh(device)

    return DeviceItem(
        id=device.id,
        device_identifier=device.device_identifier,
        device_type=device.device_type,
        registered=device.registered,
        trust_level=device.trust_level,
        owner_username=device.owner.username if device.owner else None,
        status=device.status,
        first_seen=device.first_seen,
        last_seen=device.last_seen,
    )
