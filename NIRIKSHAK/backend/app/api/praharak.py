import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.praharak import ExternalSignal, CircuitBreakerState, CrossDomainIncident
from app.schemas.praharak import (
    ExternalSignalCreateRequest,
    ExternalSignalResponse,
    CircuitBreakerStatusResponse,
    CircuitBreakerResetRequest,
    CrossDomainIncidentResponse,
    PraharakScenarioTriggerRequest,
    PraharakScenarioTriggerResponse,
)
from app.services.praharak_service import PraharakService
from app.services.event_service import EventService
from app.schemas.event import EventCreateRequest
from app.engines.praharak.crypto_engine import CryptoEngine

router = APIRouter(prefix="/praharak", tags=["PRAHARAK Outsider Risk"])


@router.post("/signals", response_model=ExternalSignalResponse, status_code=status.HTTP_201_CREATED)
async def ingest_external_signal(
    payload: ExternalSignalCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ingests an inbound external signal, validates cryptographic signature, and computes threat risk."""
    signal = await PraharakService.ingest_signal(db, payload)
    return ExternalSignalResponse(
        id=signal.id,
        signal_identifier=signal.signal_identifier,
        timestamp=signal.timestamp,
        source_ip=signal.source_ip,
        source_asn=signal.source_asn,
        target_service=signal.target_service,
        command_type=signal.command_type,
        raw_envelope=signal.raw_envelope,
        signature_valid=signal.signature_valid,
        signature_algorithm=signal.signature_algorithm,
        risk_score=signal.risk_score,
        risk_tier=signal.risk_tier,
        disposition=signal.disposition,
        factors=signal.factors,
        audit_hash=signal.audit_hash,
        created_at=signal.created_at,
    )


@router.get("/signals", response_model=List[ExternalSignalResponse])
async def list_external_signals(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    risk_tier: Optional[str] = None,
    disposition: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lists ingested external signals with optional filtering."""
    signals = await PraharakService.get_signals(db, limit, offset, risk_tier, disposition)
    return [
        ExternalSignalResponse(
            id=s.id,
            signal_identifier=s.signal_identifier,
            timestamp=s.timestamp,
            source_ip=s.source_ip,
            source_asn=s.source_asn,
            target_service=s.target_service,
            command_type=s.command_type,
            raw_envelope=s.raw_envelope,
            signature_valid=s.signature_valid,
            signature_algorithm=s.signature_algorithm,
            risk_score=s.risk_score,
            risk_tier=s.risk_tier,
            disposition=s.disposition,
            factors=s.factors,
            audit_hash=s.audit_hash,
            created_at=s.created_at,
        )
        for s in signals
    ]


@router.get("/signals/{signal_id}", response_model=ExternalSignalResponse)
async def get_external_signal(
    signal_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves a single external signal with its explainable factor decomposition."""
    s = await PraharakService.get_signal_by_id(db, signal_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="External signal not found")
    return ExternalSignalResponse(
        id=s.id,
        signal_identifier=s.signal_identifier,
        timestamp=s.timestamp,
        source_ip=s.source_ip,
        source_asn=s.source_asn,
        target_service=s.target_service,
        command_type=s.command_type,
        raw_envelope=s.raw_envelope,
        signature_valid=s.signature_valid,
        signature_algorithm=s.signature_algorithm,
        risk_score=s.risk_score,
        risk_tier=s.risk_tier,
        disposition=s.disposition,
        factors=s.factors,
        audit_hash=s.audit_hash,
        created_at=s.created_at,
    )


@router.get("/circuit-breaker", response_model=List[CircuitBreakerStatusResponse])
async def list_circuit_breaker_states(db: AsyncSession = Depends(get_db)):
    """Lists current state and quarantine status across monitored external traffic sources."""
    states = await PraharakService.get_circuit_breaker_states(db)
    now = datetime.now(timezone.utc)
    return [
        CircuitBreakerStatusResponse(
            id=s.id,
            source_identifier=s.source_identifier,
            state=s.state,
            request_count=s.request_count,
            window_start=s.window_start,
            trip_expires_at=s.trip_expires_at,
            is_quarantined=bool(s.trip_expires_at and s.trip_expires_at > now),
        )
        for s in states
    ]


@router.post("/circuit-breaker/reset")
async def reset_circuit_breaker(
    payload: CircuitBreakerResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Manually resets a tripped circuit breaker for an external source."""
    await PraharakService.reset_circuit_breaker(db, payload.source_identifier)
    return {"status": "SUCCESS", "message": f"Circuit breaker reset for {payload.source_identifier}"}


@router.get("/incidents", response_model=List[CrossDomainIncidentResponse])
async def list_cross_domain_incidents(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Lists unified hybrid attack incidents correlating external probes with internal anomalies."""
    incidents = await PraharakService.get_incidents(db, limit)
    return [
        CrossDomainIncidentResponse(
            id=inc.id,
            incident_identifier=inc.incident_identifier,
            external_signal_id=inc.external_signal_id,
            internal_event_id=inc.internal_event_id,
            case_id=inc.case_id,
            unified_risk_score=inc.unified_risk_score,
            attack_pattern=inc.attack_pattern,
            summary=inc.summary,
            detected_at=inc.detected_at,
        )
        for inc in incidents
    ]


@router.post("/scenarios/trigger", response_model=PraharakScenarioTriggerResponse)
async def trigger_praharak_scenario(
    payload: PraharakScenarioTriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Triggers on-demand PRAHARAK external threat scenarios."""
    scenario = payload.scenario.lower().strip()
    now = datetime.now(timezone.utc)

    if scenario in ["normal_telemetry", "normal", "scenario_1"]:
        # Scenario 1: Valid signed telemetry beacon from enrolled gateway
        nonce = f"nonce_{uuid.uuid4().hex[:8]}"
        ts_str = now.isoformat()
        payload_data = {"status": "OK", "battery": 98.4, "mode": "DEFENSE_IDLE"}
        sig = CryptoEngine.generate_hmac_signature(str(payload_data).encode(), ts_str, nonce)

        req = ExternalSignalCreateRequest(
            signal_identifier=f"SIG-NORM-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            source_ip="10.0.0.1",
            source_asn="AS13335",
            target_service="Tactical-Telemetry-Bus",
            command_type="TELEMETRY_BEACON",
            raw_envelope={
                "payload": payload_data,
                "timestamp": ts_str,
                "nonce": nonce,
                "algorithm": "HMAC_SHA256",
                "signature": sig,
            },
        )
        signal = await PraharakService.ingest_signal(db, req)
        summary = "Standard telemetry beacon arrived from enrolled defense gateway with valid HMAC-SHA256 signature. Allowed."

    elif scenario in ["spoofed_command", "spoof", "scenario_2"]:
        # Scenario 2: Spoofed tactical drone reroute command with tampered signature
        nonce = f"nonce_{uuid.uuid4().hex[:8]}"
        ts_str = now.isoformat()
        payload_data = {"drone_id": "DRONE-09", "action": "OVERRIDE_FLIGHT_PATH", "waypoint": [34.05, -118.25]}

        req = ExternalSignalCreateRequest(
            signal_identifier=f"SIG-SPOOF-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            source_ip="198.51.100.88",
            source_asn="AS-BULLETPROOF",
            target_service="Drone-C2-Gateway",
            command_type="DRONE_REROUTE",
            raw_envelope={
                "payload": payload_data,
                "timestamp": ts_str,
                "nonce": nonce,
                "algorithm": "ED25519",
                "signature": "TAMPERED_FORGED_SIGNATURE_0xDEADBEEF",
            },
        )
        signal = await PraharakService.ingest_signal(db, req)
        summary = "CRITICAL: Hostile drone reroute signal arrived from untrusted ASN with invalid signature. Rejected before execution."

    elif scenario in ["ddos_flood", "flood", "scenario_3"]:
        # Scenario 3: High-velocity command burst tripping circuit breaker
        flood_ip = f"203.0.113.{uuid.uuid4().int % 250 + 1}"
        await PraharakService.reset_circuit_breaker(db, flood_ip)

        # Ingest 16 rapid burst requests all within 5 seconds
        for i in range(16):
            t_burst = now - timedelta(seconds=0.2 * (16 - i))
            burst_req = ExternalSignalCreateRequest(
                signal_identifier=f"SIG-FLOOD-{uuid.uuid4().hex[:6].upper()}",
                timestamp=t_burst,
                source_ip=flood_ip,
                source_asn="AS40065",
                target_service="Edge-API-Gateway",
                command_type="API_BURST_QUERY",
                raw_envelope={"payload": f"burst_request_{i}"},
            )
            await PraharakService.ingest_signal(db, burst_req)

        # 17th request trips or hits active quarantine
        final_req = ExternalSignalCreateRequest(
            signal_identifier=f"SIG-FLOOD-TRIP-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            source_ip=flood_ip,
            source_asn="AS40065",
            target_service="Edge-API-Gateway",
            command_type="API_BURST_QUERY",
            raw_envelope={"payload": "burst_request_final"},
        )
        signal = await PraharakService.ingest_signal(db, final_req)
        summary = f"Mass request flood detected from {flood_ip}. Sliding-window circuit breaker TRIPPED to OPEN. 15-minute quarantine active."

    elif scenario in ["hybrid_coordinated_attack", "hybrid", "scenario_4"]:
        # Scenario 4: External recon followed immediately by internal credential abuse
        attacker_ip = "198.51.100.77"

        # Step A: Ingest internal anomalous access event (e.g. USER-004 exfiltrating data)
        int_req = EventCreateRequest(
            event_id=f"evt_hybrid_{uuid.uuid4().hex[:6]}",
            timestamp=now - timedelta(minutes=5),
            user_identifier="USER-004",
            device_identifier="DEV-104",
            resource_identifier="Operational Repository A",
            action="EXPORT",
            result="SUCCESS",
            data_volume=1048576000,  # 1 GB
            source_context={"mfa_verified": False, "corporate_network": False, "client_ip": attacker_ip},
        )
        await EventService.ingest_event(db, int_req)

        # Step B: External reconnaissance probe on authentication gateway
        ext_req = ExternalSignalCreateRequest(
            signal_identifier=f"SIG-HYBRID-{uuid.uuid4().hex[:6].upper()}",
            timestamp=now,
            source_ip=attacker_ip,
            source_asn="AS40065",
            target_service="Operational-Auth-Gateway",
            command_type="AUTH_BRUTE_FORCE",
            raw_envelope={"payload": "password_spray_batch"},
        )
        signal = await PraharakService.ingest_signal(db, ext_req)
        summary = (
            f"COORDINATED HYBRID ATTACK FUSION: External brute-force probe from {attacker_ip} "
            "directly correlated with internal credential exfiltration by USER-004. Cross-Domain Nexus incident generated."
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown scenario '{payload.scenario}'. Supported: 'normal_telemetry', 'spoofed_command', 'ddos_flood', 'hybrid_coordinated_attack'.",
        )

    # Check if a cross-domain incident was created for this signal
    inc_stmt = select(CrossDomainIncident).where(CrossDomainIncident.external_signal_id == signal.id)
    inc_res = await db.execute(inc_stmt)
    incident = inc_res.scalar_one_or_none()

    cb_tripped = (
        (signal.disposition == "BLOCKED" and signal.risk_tier == "CRITICAL")
        or (signal.risk_score >= 85.0)
        or any("CIRCUIT_BREAKER" in f.get("factor", "") for f in (signal.factors or []))
    )

    return PraharakScenarioTriggerResponse(
        scenario=scenario,
        signal_identifier=signal.signal_identifier,
        risk_score=signal.risk_score,
        risk_tier=signal.risk_tier,
        disposition=signal.disposition,
        circuit_breaker_tripped=cb_tripped,
        cross_domain_incident_id=incident.incident_identifier if incident else None,
        summary=summary,
    )
