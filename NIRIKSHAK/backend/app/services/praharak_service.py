import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.praharak import ExternalSignal, CircuitBreakerState, CrossDomainIncident
from app.schemas.praharak import ExternalSignalCreateRequest
from app.engines.praharak.praharak_risk_engine import PraharakRiskEngine
from app.engines.praharak.circuit_breaker_engine import CircuitBreakerEngine
from app.engines.praharak.cross_domain_engine import CrossDomainEngine

logger = logging.getLogger(__name__)


class PraharakService:
    @staticmethod
    async def get_latest_audit_hash(db: AsyncSession) -> str:
        """Retrieves previous audit hash for immutable SHA-256 hash chaining."""
        stmt = select(ExternalSignal.audit_hash).order_by(ExternalSignal.created_at.desc()).limit(1)
        res = await db.execute(stmt)
        prev_hash = res.scalar_one_or_none()
        return prev_hash if prev_hash else "0" * 64

    @classmethod
    async def ingest_signal(cls, db: AsyncSession, payload: ExternalSignalCreateRequest) -> ExternalSignal:
        now = payload.timestamp or datetime.now(timezone.utc)
        signal_id = payload.signal_identifier or f"SIG-EXT-{uuid.uuid4().hex[:8].upper()}"

        # 1. Run Praharak Risk Engine
        (
            total_score,
            risk_tier,
            disposition,
            sig_valid,
            sig_algo,
            is_tripped,
            factors,
        ) = PraharakRiskEngine.evaluate(
            source_ip=payload.source_ip,
            source_asn=payload.source_asn,
            target_service=payload.target_service,
            command_type=payload.command_type,
            raw_envelope=payload.raw_envelope,
            current_time=now,
        )

        # 2. Compute SHA-256 Hash Chain
        prev_hash = await cls.get_latest_audit_hash(db)
        payload_hash = hashlib.sha256(str(payload.raw_envelope).encode()).hexdigest()
        raw_chain = f"{prev_hash}|{now.isoformat()}|{signal_id}|{payload_hash}|{disposition}"
        current_audit_hash = hashlib.sha256(raw_chain.encode()).hexdigest()

        # 3. Create ExternalSignal record
        signal = ExternalSignal(
            id=str(uuid.uuid4()),
            signal_identifier=signal_id,
            timestamp=now,
            source_ip=payload.source_ip,
            source_asn=payload.source_asn,
            target_service=payload.target_service,
            command_type=payload.command_type,
            raw_envelope=payload.raw_envelope,
            signature_valid=sig_valid,
            signature_algorithm=sig_algo,
            risk_score=total_score,
            risk_tier=risk_tier,
            disposition=disposition,
            factors=[f.model_dump() for f in factors],
            audit_hash=current_audit_hash,
            created_at=datetime.now(timezone.utc),
        )
        db.add(signal)
        await db.flush()

        # 4. Sync Circuit Breaker State in DB
        cb_state = CircuitBreakerEngine.get_state(payload.source_ip)
        cb_stmt = select(CircuitBreakerState).where(CircuitBreakerState.source_identifier == payload.source_ip)
        cb_res = await db.execute(cb_stmt)
        db_cb = cb_res.scalar_one_or_none()

        if not db_cb:
            db_cb = CircuitBreakerState(
                id=str(uuid.uuid4()),
                source_identifier=payload.source_ip,
                state=cb_state["state"],
                request_count=cb_state.get("request_count", 1),
                window_start=cb_state.get("window_start") or now,
                trip_expires_at=cb_state.get("trip_expires_at"),
            )
            db.add(db_cb)
        else:
            db_cb.state = cb_state["state"]
            db_cb.request_count = cb_state.get("request_count", db_cb.request_count + 1)
            db_cb.trip_expires_at = cb_state.get("trip_expires_at")
        await db.flush()

        # 5. Evaluate Cross-Domain Correlation Nexus
        incident = await CrossDomainEngine.evaluate_correlation(db, signal)
        if incident:
            signal.risk_score = incident.unified_risk_score
            signal.risk_tier = "CRITICAL"
            signal.disposition = "BLOCKED"
            signal.factors = (signal.factors or []) + [
                {
                    "factor": "CROSS_DOMAIN_HYBRID_INCIDENT_CORRELATED",
                    "subscore": 100.0,
                    "weight": 0.35,
                    "contribution": 35.0,
                    "explanation": incident.summary,
                    "details": {
                        "incident_id": incident.incident_identifier,
                        "pattern": incident.attack_pattern,
                    },
                }
            ]

        await db.commit()
        await db.refresh(signal)
        return signal

    @staticmethod
    async def get_signals(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        risk_tier: Optional[str] = None,
        disposition: Optional[str] = None,
    ) -> List[ExternalSignal]:
        stmt = select(ExternalSignal).order_by(ExternalSignal.timestamp.desc())
        if risk_tier:
            stmt = stmt.where(ExternalSignal.risk_tier == risk_tier.upper())
        if disposition:
            stmt = stmt.where(ExternalSignal.disposition == disposition.upper())
        stmt = stmt.offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_signal_by_id(db: AsyncSession, signal_id: str) -> Optional[ExternalSignal]:
        stmt = select(ExternalSignal).where(
            (ExternalSignal.id == signal_id) | (ExternalSignal.signal_identifier == signal_id)
        ).options(selectinload(ExternalSignal.incidents))
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_circuit_breaker_states(db: AsyncSession) -> List[CircuitBreakerState]:
        stmt = select(CircuitBreakerState).order_by(CircuitBreakerState.updated_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def reset_circuit_breaker(db: AsyncSession, source_identifier: str) -> bool:
        CircuitBreakerEngine.reset_state(source_identifier)
        stmt = select(CircuitBreakerState).where(CircuitBreakerState.source_identifier == source_identifier)
        res = await db.execute(stmt)
        cb = res.scalar_one_or_none()
        if cb:
            cb.state = "CLOSED"
            cb.request_count = 0
            cb.trip_expires_at = None
            await db.commit()
        return True

    @staticmethod
    async def get_incidents(db: AsyncSession, limit: int = 20) -> List[CrossDomainIncident]:
        stmt = (
            select(CrossDomainIncident)
            .order_by(CrossDomainIncident.detected_at.desc())
            .options(
                selectinload(CrossDomainIncident.external_signal),
                selectinload(CrossDomainIncident.internal_event),
                selectinload(CrossDomainIncident.case),
            )
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
