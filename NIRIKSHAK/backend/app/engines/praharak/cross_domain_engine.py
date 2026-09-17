import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import AccessEvent
from app.models.praharak import ExternalSignal, CrossDomainIncident
from app.models.case import SecurityCase

logger = logging.getLogger(__name__)


class CrossDomainEngine:
    """The Shared Nexus Core: Fuses external reconnaissance/probes with internal credential telemetry."""

    @staticmethod
    async def evaluate_correlation(
        db: AsyncSession,
        external_signal: ExternalSignal,
        correlation_window_minutes: int = 30,
    ) -> Optional[CrossDomainIncident]:
        """
        Inspects internal AccessEvents within a sliding 30-minute window for matching anomalous activity.
        """
        signal_time = external_signal.timestamp
        window_start = signal_time - timedelta(minutes=correlation_window_minutes)
        window_end = signal_time + timedelta(minutes=correlation_window_minutes)

        # Query recent internal access events
        stmt = (
            select(AccessEvent)
            .where(AccessEvent.timestamp >= window_start, AccessEvent.timestamp <= window_end)
            .options(
                selectinload(AccessEvent.user),
                selectinload(AccessEvent.resource),
                selectinload(AccessEvent.risk_score),
            )
            .order_by(AccessEvent.timestamp.desc())
        )
        result = await db.execute(stmt)
        recent_events = result.scalars().all()

        if not recent_events:
            return None

        # Look for events that are suspicious or targeting related resources
        candidate_event = None
        for evt in recent_events:
            score = evt.risk_score.total_score if evt.risk_score else 0.0
            # Condition 1: Internal event has elevated risk (>= 40.0)
            # Condition 2: Or internal event IP matches external IP
            client_ip = (evt.source_context or {}).get("client_ip", "")
            is_same_ip = client_ip and client_ip == external_signal.source_ip
            is_off_hours_or_elevated = score >= 50.0

            if is_same_ip or is_off_hours_or_elevated:
                candidate_event = evt
                break

        if not candidate_event:
            return None

        internal_score = candidate_event.risk_score.total_score if candidate_event.risk_score else 45.0
        ext_score = external_signal.risk_score

        # Apply Cross-Domain Nexus Multiplier
        base_max = max(ext_score, internal_score)
        unified_score = round(min(100.0, max(85.0, base_max * 1.35)), 1)

        user_ident = candidate_event.user.external_identifier if candidate_event.user else "UNKNOWN_USER"
        resource_name = candidate_event.resource.name if candidate_event.resource else "INTERNAL_RESOURCE"

        attack_pattern = "HYBRID_RECON_CREDENTIAL_ABUSE"
        summary = (
            f"COORDINATED HYBRID ATTACK DETECTED: External probe/command from '{external_signal.source_ip}' "
            f"directly correlated with internal anomalous access by '{user_ident}' targeting '{resource_name}'. "
            f"Unified risk amplified from {base_max} to {unified_score} (CRITICAL)."
        )

        # Check or create SecurityCase
        case_stmt = select(SecurityCase).where(SecurityCase.event_id == candidate_event.id)
        case_res = await db.execute(case_stmt)
        existing_case = case_res.scalar_one_or_none()

        case_id = existing_case.id if existing_case else None
        if not existing_case:
            import uuid
            new_case = SecurityCase(
                id=str(uuid.uuid4()),
                case_identifier=f"CASE-HYBRID-{uuid.uuid4().hex[:6].upper()}",
                status="OPEN",
                severity="CRITICAL",
                primary_user_id=candidate_event.user_id,
                event_id=candidate_event.id,
                opened_at=datetime.now(timezone.utc),
            )
            db.add(new_case)
            await db.flush()
            case_id = new_case.id

        import uuid
        incident = CrossDomainIncident(
            id=str(uuid.uuid4()),
            incident_identifier=f"INC-HYBRID-{uuid.uuid4().hex[:6].upper()}",
            external_signal_id=external_signal.id,
            internal_event_id=candidate_event.id,
            case_id=case_id,
            unified_risk_score=unified_score,
            attack_pattern=attack_pattern,
            summary=summary,
            detected_at=datetime.now(timezone.utc),
        )
        db.add(incident)
        await db.flush()

        logger.warning(f"PRAHARAK NEXUS: Created CrossDomainIncident {incident.incident_identifier} with score {unified_score}")
        return incident
