import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.event import EventCreateRequest, ScenarioTriggerRequest, ScenarioTriggerResponse
from app.services.event_service import EventService
from app.engines.explanation_engine import ExplanationEngine

router = APIRouter(prefix="/scenarios", tags=["Scenario Simulator"])


@router.post("/trigger", response_model=ScenarioTriggerResponse)
async def trigger_demo_scenario(payload: ScenarioTriggerRequest, db: AsyncSession = Depends(get_db)):
    """Triggers a pre-scripted on-demand demo scenario (normal, off_hours, or exfiltration)."""
    scenario = payload.scenario.lower().strip()
    now = datetime.now(timezone.utc)

    if scenario in ["normal", "scenario_1", "1"]:
        # Scenario 1: Normal working read by USER-001 during regular hours with MFA
        event_time = now.replace(hour=11, minute=30, second=0, microsecond=0)
        req = EventCreateRequest(
            event_id=f"evt_norm_{uuid.uuid4().hex[:6]}",
            timestamp=event_time,
            user_identifier="USER-001",
            device_identifier="DEV-101",
            resource_identifier="Operational Repository A",
            action="READ",
            result="SUCCESS",
            data_volume=10485760,  # 10 MB
            source_context={"mfa_verified": True, "corporate_network": True, "client_ip": "10.0.4.15"},
        )
    elif scenario in ["off_hours", "scenario_2", "2"]:
        # Scenario 2: 02:30 AM access by Engineering user to Defense repo without MFA
        event_time = now.replace(hour=2, minute=30, second=0, microsecond=0)
        req = EventCreateRequest(
            event_id=f"evt_offhr_{uuid.uuid4().hex[:6]}",
            timestamp=event_time,
            user_identifier="USER-002",
            device_identifier="DEV-102",
            resource_identifier="Operational Repository A",
            action="READ",
            result="SUCCESS",
            data_volume=12582912,  # 12 MB
            source_context={"mfa_verified": False, "corporate_network": True, "client_ip": "10.0.1.25"},
        )
    elif scenario in ["exfiltration", "scenario_3", "3"]:
        # Scenario 3: Bulk data exfiltration from unregistered DEV-999 at 03:15 AM
        event_time = now.replace(hour=3, minute=15, second=0, microsecond=0)
        req = EventCreateRequest(
            event_id=f"evt_exfil_{uuid.uuid4().hex[:6]}",
            timestamp=event_time,
            user_identifier="USER-003",
            device_identifier="DEV-999",
            resource_identifier="Personnel Security Repository D",
            action="EXPORT",
            result="SUCCESS",
            data_volume=2684354560,  # 2.5 GB
            source_context={"mfa_verified": False, "corporate_network": False, "client_ip": "198.51.100.42"},
        )
    elif scenario in ["kill_chain", "killchain", "scenario_4", "4"]:
        # Scenario 4: Multi-Stage Kill Chain (Recon -> Enumeration -> Traversal -> Exfiltration)
        from datetime import timedelta
        # Stage 1: Off-hours recon from external IP
        t1 = now - timedelta(minutes=12)
        await EventService.ingest_event(db, EventCreateRequest(
            event_id=f"evt_kc1_{uuid.uuid4().hex[:6]}",
            timestamp=t1,
            user_identifier="USER-004",
            device_identifier="DEV-104",
            resource_identifier="Public Documentation E",
            action="READ",
            result="SUCCESS",
            data_volume=524288,
            source_context={"mfa_verified": True, "corporate_network": False, "client_ip": "198.51.100.77"},
        ))

        # Stage 2: Cross-repository crawl
        t2 = now - timedelta(minutes=8)
        await EventService.ingest_event(db, EventCreateRequest(
            event_id=f"evt_kc2_{uuid.uuid4().hex[:6]}",
            timestamp=t2,
            user_identifier="USER-004",
            device_identifier="DEV-104",
            resource_identifier="Engineering Repository B",
            action="READ",
            result="SUCCESS",
            data_volume=2097152,
            source_context={"mfa_verified": True, "corporate_network": False, "client_ip": "198.51.100.77"},
        ))

        # Stage 3: Privilege traversal to CRITICAL operational repository without MFA
        t3 = now - timedelta(minutes=3)
        await EventService.ingest_event(db, EventCreateRequest(
            event_id=f"evt_kc3_{uuid.uuid4().hex[:6]}",
            timestamp=t3,
            user_identifier="USER-004",
            device_identifier="DEV-104",
            resource_identifier="Operational Repository A",
            action="READ",
            result="SUCCESS",
            data_volume=8388608,
            source_context={"mfa_verified": False, "corporate_network": False, "client_ip": "198.51.100.77"},
        ))

        # Stage 4: High-volume bulk export trigger
        req = EventCreateRequest(
            event_id=f"evt_kc4_{uuid.uuid4().hex[:6]}",
            timestamp=now,
            user_identifier="USER-004",
            device_identifier="DEV-104",
            resource_identifier="Operational Repository A",
            action="EXPORT",
            result="SUCCESS",
            data_volume=1887436800,  # 1.8 GB
            source_context={"mfa_verified": False, "corporate_network": False, "client_ip": "198.51.100.77"},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown scenario '{payload.scenario}'. Supported scenarios: 'normal', 'off_hours', 'exfiltration', 'kill_chain'.",
        )

    # Ingest event through standard analytical pipeline
    result = await EventService.ingest_event(db, req)

    # Generate executive narrative
    narrative = ExplanationEngine.generate_narrative_summary(
        factors=result["factors"],
        risk_level=result["risk_level"],
    )

    return ScenarioTriggerResponse(
        scenario=scenario,
        event_id=result["event_id"],
        internal_id=result["internal_id"],
        total_score=result["total_score"],
        risk_level=result["risk_level"],
        case_created=result["case_created"],
        case_id=result["case_id"],
        summary=narrative,
    )
