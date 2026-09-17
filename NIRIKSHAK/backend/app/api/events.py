from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.event import AccessEvent
from app.models.risk import RiskScore
from app.models.case import SecurityCase
from app.schemas.event import EventCreateRequest, EventListItem
from app.schemas.risk import EventExplanationResponse, FactorDetail
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events & Telemetry"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def ingest_access_event(payload: EventCreateRequest, db: AsyncSession = Depends(get_db)):
    """Ingests a telemetry event, computes deterministic multi-factor risk, and records case if elevated."""
    result = await EventService.ingest_event(db, payload)
    return result


@router.get("", response_model=List[EventListItem])
async def list_events(
    limit: int = Query(default=50, ge=1, le=200),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk level (LOW, MODERATE, HIGH, CRITICAL)"),
    db: AsyncSession = Depends(get_db),
):
    """Lists recent access telemetry events with evaluated risk scores and case references."""
    stmt = (
        select(AccessEvent)
        .options(
            selectinload(AccessEvent.user),
            selectinload(AccessEvent.device),
            selectinload(AccessEvent.resource),
            selectinload(AccessEvent.risk_score),
        )
        .order_by(desc(AccessEvent.timestamp))
        .limit(limit)
    )

    result = await db.execute(stmt)
    events = result.scalars().all()

    # Pre-fetch active cases for these events
    event_ids = [e.id for e in events]
    cases_stmt = select(SecurityCase).where(SecurityCase.event_id.in_(event_ids))
    cases_res = await db.execute(cases_stmt)
    event_to_case = {c.event_id: c.id for c in cases_res.scalars().all()}

    output = []
    for e in events:
        total_score = e.risk_score.total_score if e.risk_score else 0.0
        level = e.risk_score.risk_level if e.risk_score else "LOW"

        if risk_level and level.upper() != risk_level.upper():
            continue

        output.append(
            EventListItem(
                id=e.id,
                event_id=e.event_id,
                timestamp=e.timestamp,
                user_id=e.user_id,
                user_identifier=e.user.external_identifier if e.user else "UNKNOWN",
                department=e.user.department if e.user else "UNKNOWN",
                device_identifier=e.device.device_identifier if e.device else "UNKNOWN",
                resource_name=e.resource.name if e.resource else "UNKNOWN",
                action=e.action,
                result=e.result,
                data_volume=e.data_volume,
                risk_score=total_score,
                risk_level=level,
                case_id=event_to_case.get(e.id),
            )
        )

    return output


@router.get("/{event_id}/explanation", response_model=EventExplanationResponse)
async def get_event_explanation(event_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves the granular explainability breakdown and factor contributions for an event."""
    stmt = (
        select(RiskScore)
        .where(
            (RiskScore.event_id == event_id) | (RiskScore.id == event_id)
        )
        .options(selectinload(RiskScore.factors))
    )
    result = await db.execute(stmt)
    risk_score = result.scalar_one_or_none()

    if not risk_score:
        # Check by AccessEvent.event_id
        event_stmt = select(AccessEvent).where(AccessEvent.event_id == event_id).options(selectinload(AccessEvent.risk_score))
        ev_res = await db.execute(event_stmt)
        ev = ev_res.scalar_one_or_none()
        if ev and ev.risk_score:
            risk_score = ev.risk_score
            stmt_f = select(RiskScore).where(RiskScore.id == risk_score.id).options(selectinload(RiskScore.factors))
            risk_score = (await db.execute(stmt_f)).scalar_one_or_none()

    if not risk_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk evaluation or factor explanation found for event '{event_id}'.",
        )

    factors_detail = [
        FactorDetail(
            factor=f.factor,
            subscore=f.subscore,
            weight=f.weight,
            contribution=f.contribution,
            explanation=f.explanation,
            details=f.details or {},
        )
        for f in risk_score.factors
    ]
    # Sort descending by contribution
    factors_detail.sort(key=lambda x: x.contribution, reverse=True)

    return EventExplanationResponse(
        event_id=event_id,
        total_score=risk_score.total_score,
        risk_level=risk_score.risk_level,
        factors=factors_detail,
    )
