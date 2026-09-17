import logging
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource, ResourceClassification
from app.models.baseline import BehaviorBaseline
from app.models.event import AccessEvent
from app.models.risk import RiskScore, RiskFactor
from app.models.case import SecurityCase
from app.schemas.event import EventCreateRequest
from app.engines.risk_engine import RiskEngine

logger = logging.getLogger(__name__)


class EventService:
    @staticmethod
    async def ingest_event(db: AsyncSession, payload: EventCreateRequest) -> dict:
        """Ingests, validates, evaluates risk, and persists an access event."""
        # 1. Resolve User & Baseline
        stmt_user = (
            select(User)
            .where(
                or_(
                    User.id == payload.user_identifier,
                    User.external_identifier == payload.user_identifier,
                    User.username == payload.user_identifier,
                )
            )
            .options(selectinload(User.baseline))
        )
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{payload.user_identifier}' not found in registry.",
            )

        # 2. Resolve Device (or dynamically register unknown device)
        stmt_device = select(Device).where(
            or_(
                Device.id == payload.device_identifier,
                Device.device_identifier == payload.device_identifier,
            )
        )
        res_device = await db.execute(stmt_device)
        device = res_device.scalar_one_or_none()

        if not device:
            # Create unregistered untrusted endpoint record
            device = Device(
                id=str(uuid.uuid4()),
                device_identifier=payload.device_identifier,
                owner_user_id=None,
                device_type="UNKNOWN",
                registered=False,
                trust_level="LOW",
                status="ACTIVE",
            )
            db.add(device)
            await db.flush()

        # 3. Resolve Resource & Classification
        stmt_resource = (
            select(Resource)
            .where(
                or_(
                    Resource.id == payload.resource_identifier,
                    Resource.name == payload.resource_identifier,
                )
            )
            .options(selectinload(Resource.classification))
        )
        res_resource = await db.execute(stmt_resource)
        resource = res_resource.scalar_one_or_none()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource '{payload.resource_identifier}' not found in registry.",
            )

        classification = resource.classification

        # 4. Fetch Active Policies & Recent User Events (for temporal correlation)
        from datetime import timedelta
        from app.services.policy_service import PolicyService

        policies = await PolicyService.get_all_policies(db)
        event_time = payload.timestamp or datetime.now(timezone.utc)
        window_start = event_time - timedelta(minutes=30)

        stmt_recent = (
            select(AccessEvent)
            .where(
                AccessEvent.user_id == user.id,
                AccessEvent.timestamp >= window_start,
            )
            .order_by(AccessEvent.timestamp.desc())
        )
        res_recent = await db.execute(stmt_recent)
        recent_events = res_recent.scalars().all()

        # 5. Evaluate Risk using 6-Signal Comprehensive Engine (Identity, Device, Sensitivity, Behavior, ML Anomaly, Correlation)
        risk_result = RiskEngine.evaluate_event(
            user=user,
            device=device,
            resource=resource,
            classification=classification,
            baseline=user.baseline,
            action=payload.action,
            timestamp=event_time,
            data_volume=payload.data_volume,
            source_context=payload.source_context,
            custom_weights=policies,
            custom_thresholds=policies,
            recent_events=recent_events,
            enable_ml=True,
        )

        # 6. Persist AccessEvent
        event_record = AccessEvent(
            id=str(uuid.uuid4()),
            event_id=payload.event_id or f"evt_{uuid.uuid4().hex[:10]}",
            timestamp=event_time,
            user_id=user.id,
            device_id=device.id,
            resource_id=resource.id,
            session_id=payload.session_id or f"sess_{uuid.uuid4().hex[:8]}",
            action=payload.action.upper(),
            result=payload.result.upper(),
            data_volume=payload.data_volume,
            source_context=payload.source_context,
        )
        db.add(event_record)
        await db.flush()

        # 7. Persist RiskScore
        risk_score_record = RiskScore(
            id=str(uuid.uuid4()),
            event_id=event_record.id,
            total_score=risk_result.total_score,
            risk_level=risk_result.risk_level,
            identity_score=risk_result.identity_score,
            device_score=risk_result.device_score,
            sensitivity_score=risk_result.sensitivity_score,
            behavior_score=risk_result.behavior_score,
            anomaly_score=risk_result.anomaly_score or 0.0,
            correlation_score=risk_result.correlation_score or 0.0,
        )
        db.add(risk_score_record)
        await db.flush()

        # 7. Persist RiskFactors
        for factor in risk_result.factors:
            factor_record = RiskFactor(
                id=str(uuid.uuid4()),
                risk_score_id=risk_score_record.id,
                factor=factor.factor,
                subscore=factor.subscore,
                weight=factor.weight,
                contribution=factor.contribution,
                explanation=factor.explanation,
                details=factor.details,
            )
            db.add(factor_record)

        # 8. Auto-Create SecurityCase if HIGH or CRITICAL
        case_created = False
        case_id = None
        if risk_result.risk_level in ["HIGH", "CRITICAL"]:
            case_id = str(uuid.uuid4())
            case_identifier = f"CASE-{datetime.now().year}-{str(uuid.uuid4().hex[:6]).upper()}"
            security_case = SecurityCase(
                id=case_id,
                case_identifier=case_identifier,
                status="OPEN",
                severity=risk_result.risk_level,
                primary_user_id=user.id,
                event_id=event_record.id,
            )
            db.add(security_case)
            case_created = True

        await db.commit()

        logger.info(
            f"Ingested event '{event_record.event_id}' for {user.external_identifier} "
            f"-> Risk: {risk_result.total_score} ({risk_result.risk_level}), Case Created: {case_created}"
        )

        return {
            "internal_id": event_record.id,
            "event_id": event_record.event_id,
            "total_score": risk_result.total_score,
            "risk_level": risk_result.risk_level,
            "case_created": case_created,
            "case_id": case_id,
            "user_identifier": user.external_identifier,
            "resource_name": resource.name,
            "factors": risk_result.factors,
        }
