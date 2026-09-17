import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.case import SecurityCase
from app.models.event import AccessEvent
from app.models.risk import RiskScore
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.case import CaseListItem, CaseDetailResponse, CaseReviewRequest, CaseReviewResponse
from app.schemas.risk import FactorDetail

router = APIRouter(prefix="/cases", tags=["Case Management & Human Review"])
security_scheme = HTTPBearer(auto_error=False)


@router.get("", response_model=List[CaseListItem])
async def list_cases(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status: OPEN, DISMISSED, ESCALATED"),
    severity_filter: Optional[str] = Query(default=None, alias="severity", description="Filter by severity: HIGH, CRITICAL"),
    db: AsyncSession = Depends(get_db),
):
    """Lists all security cases requiring human analyst triage."""
    stmt = (
        select(SecurityCase)
        .options(
            selectinload(SecurityCase.primary_user),
            selectinload(SecurityCase.event).selectinload(AccessEvent.resource),
            selectinload(SecurityCase.event).selectinload(AccessEvent.risk_score),
        )
        .order_by(desc(SecurityCase.opened_at))
    )

    result = await db.execute(stmt)
    cases = result.scalars().all()

    output = []
    for c in cases:
        if status_filter and c.status.upper() != status_filter.upper():
            continue
        if severity_filter and c.severity.upper() != severity_filter.upper():
            continue

        resource_name = None
        risk_score = None
        if c.event:
            resource_name = c.event.resource.name if c.event.resource else None
            risk_score = c.event.risk_score.total_score if c.event.risk_score else None

        output.append(
            CaseListItem(
                id=c.id,
                case_identifier=c.case_identifier,
                status=c.status,
                severity=c.severity,
                opened_at=c.opened_at,
                primary_user_identifier=c.primary_user.external_identifier if c.primary_user else "UNKNOWN",
                department=c.primary_user.department if c.primary_user else "UNKNOWN",
                event_id=c.event.event_id if c.event else None,
                resource_name=resource_name,
                risk_score=risk_score,
            )
        )

    return output


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case_detail(case_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full case details including correlated event, factor breakdown, and audit history."""
    stmt = (
        select(SecurityCase)
        .where(
            (SecurityCase.id == case_id) | (SecurityCase.case_identifier == case_id)
        )
        .options(
            selectinload(SecurityCase.primary_user),
            selectinload(SecurityCase.assigned_analyst),
            selectinload(SecurityCase.event).selectinload(AccessEvent.resource),
            selectinload(SecurityCase.event).selectinload(AccessEvent.device),
            selectinload(SecurityCase.event).selectinload(AccessEvent.risk_score).selectinload(RiskScore.factors),
        )
    )

    result = await db.execute(stmt)
    case_obj = result.scalar_one_or_none()

    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    # Fetch audit history for this case
    audit_stmt = (
        select(AuditLog)
        .where(AuditLog.target_id == case_obj.id)
        .order_by(desc(AuditLog.timestamp))
    )
    audit_res = await db.execute(audit_stmt)
    audit_logs = audit_res.scalars().all()

    audit_history = [
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "actor": a.actor_username,
            "action": a.action,
            "justification": a.justification,
        }
        for a in audit_logs
    ]

    factors: List[FactorDetail] = []
    total_score = None
    risk_level = None

    if case_obj.event and case_obj.event.risk_score:
        rs = case_obj.event.risk_score
        total_score = rs.total_score
        risk_level = rs.risk_level
        factors = [
            FactorDetail(
                factor=f.factor,
                subscore=f.subscore,
                weight=f.weight,
                contribution=f.contribution,
                explanation=f.explanation,
                details=f.details or {},
            )
            for f in rs.factors
        ]
        factors.sort(key=lambda x: x.contribution, reverse=True)

    return CaseDetailResponse(
        id=case_obj.id,
        case_identifier=case_obj.case_identifier,
        status=case_obj.status,
        severity=case_obj.severity,
        opened_at=case_obj.opened_at,
        updated_at=case_obj.updated_at,
        primary_user_id=case_obj.primary_user_id,
        primary_user_identifier=case_obj.primary_user.external_identifier if case_obj.primary_user else "UNKNOWN",
        department=case_obj.primary_user.department if case_obj.primary_user else "UNKNOWN",
        assigned_analyst=case_obj.assigned_analyst.username if case_obj.assigned_analyst else None,
        event_id=case_obj.event.event_id if case_obj.event else None,
        event_timestamp=case_obj.event.timestamp if case_obj.event else None,
        resource_name=case_obj.event.resource.name if (case_obj.event and case_obj.event.resource) else None,
        device_identifier=case_obj.event.device.device_identifier if (case_obj.event and case_obj.event.device) else None,
        total_score=total_score,
        risk_level=risk_level,
        factors=factors,
        audit_history=audit_history,
    )


@router.post("/{case_id}/review", response_model=CaseReviewResponse)
async def review_case(
    case_id: str,
    payload: CaseReviewRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Executes a human review action (DISMISS or ESCALATE) with mandatory justification and audit logging."""
    action = payload.action.upper().strip()
    if action not in ["DISMISS", "ESCALATE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review action. Allowed actions are 'DISMISS' or 'ESCALATE'.",
        )

    stmt = (
        select(SecurityCase)
        .where((SecurityCase.id == case_id) | (SecurityCase.case_identifier == case_id))
    )
    result = await db.execute(stmt)
    case_obj = result.scalar_one_or_none()

    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    # Determine acting analyst identity from token or default seeded demo analyst
    analyst_id = None
    analyst_username = "analyst_sarah"
    if credentials:
        token_payload = decode_access_token(credentials.credentials)
        if token_payload:
            analyst_username = token_payload.get("sub", "analyst_sarah")
            analyst_id = token_payload.get("user_id")

    if not analyst_id:
        user_stmt = select(User).where(User.username == analyst_username)
        u_res = await db.execute(user_stmt)
        user_rec = u_res.scalar_one_or_none()
        if user_rec:
            analyst_id = user_rec.id

    previous_status = case_obj.status
    new_status = "DISMISSED" if action == "DISMISS" else "ESCALATED"

    # 1. Update Case
    case_obj.status = new_status
    case_obj.assigned_analyst_id = analyst_id
    case_obj.updated_at = datetime.now(timezone.utc)

    # 2. Atomically Write Immutable Audit Log
    audit_id = str(uuid.uuid4())
    audit_entry = AuditLog(
        id=audit_id,
        timestamp=datetime.now(timezone.utc),
        actor_id=analyst_id,
        actor_username=analyst_username,
        action=f"case:{action.lower()}",
        target_entity="security_cases",
        target_id=case_obj.id,
        justification=payload.justification,
        details={
            "case_identifier": case_obj.case_identifier,
            "previous_status": previous_status,
            "new_status": new_status,
            "action": action,
        },
    )
    db.add(audit_entry)

    await db.commit()

    return CaseReviewResponse(
        case_id=case_obj.id,
        case_identifier=case_obj.case_identifier,
        status=new_status,
        reviewed_by=analyst_username,
        justification=payload.justification,
        audit_log_id=audit_id,
        timestamp=audit_entry.timestamp,
    )
