from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.audit import AuditLog
from app.schemas.case import AuditLogItem

router = APIRouter(prefix="/audit", tags=["Audit & Governance"])


@router.get("/logs", response_model=List[AuditLogItem])
async def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves the immutable audit log trail of all human review and administrative actions."""
    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [
        AuditLogItem(
            id=a.id,
            timestamp=a.timestamp,
            actor_username=a.actor_username,
            action=a.action,
            target_entity=a.target_entity,
            target_id=a.target_id,
            justification=a.justification,
            details=a.details or {},
        )
        for a in logs
    ]
