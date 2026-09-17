import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.database import Base, get_db
from app.core.seeds import seed_initial_data
from app.main import app
from app.engines.praharak.origin_engine import OriginEngine
from app.engines.praharak.crypto_engine import CryptoEngine
from app.engines.praharak.recon_engine import ReconEngine
from app.engines.praharak.circuit_breaker_engine import CircuitBreakerEngine
from app.engines.praharak.praharak_risk_engine import PraharakRiskEngine
from app.models.praharak import ExternalSignal, CrossDomainIncident, CircuitBreakerState

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client_with_db():
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    import app.core.seeds as seeds_module
    original_session = seeds_module.AsyncSessionLocal
    seeds_module.AsyncSessionLocal = async_session

    await seed_initial_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, async_session

    app.dependency_overrides.clear()
    seeds_module.AsyncSessionLocal = original_session
    await test_engine.dispose()


# ==================== ENGINE UNIT TESTS ====================

def test_origin_engine():
    # 1. Enrolled gateway / private IP -> 0 subscore
    sub, factors = OriginEngine.evaluate("10.0.0.1", "AS13335")
    assert sub == 0.0
    assert factors[0].factor == "TRUSTED_ORIGIN"

    # 2. Unknown public IP -> 35 subscore
    sub, factors = OriginEngine.evaluate("8.8.8.8", "AS15169")
    assert sub == 35.0

    # 3. Threat intel malicious subnet -> high subscore
    sub, factors = OriginEngine.evaluate("198.51.100.55", "AS40065")
    assert sub >= 85.0
    assert factors[0].factor == "UNTRUSTED_EXTERNAL_ORIGIN"


def test_crypto_engine_spoofing_detection():
    now = datetime.now(timezone.utc)
    ts_str = now.isoformat()
    nonce = f"nonce_test_{uuid.uuid4().hex[:6]}"
    payload = {"command": "DRONE_REROUTE", "waypoint": [12.9, 77.5]}

    # 1. Valid HMAC signature
    sig = CryptoEngine.generate_hmac_signature(str(payload).encode(), ts_str, nonce)
    env = {
        "payload": payload,
        "timestamp": ts_str,
        "nonce": nonce,
        "algorithm": "HMAC_SHA256",
        "signature": sig,
    }
    sub, valid, algo, factors = CryptoEngine.evaluate("DRONE_REROUTE", env, now)
    assert valid is True
    assert sub == 0.0
    assert factors[0].factor == "CRYPTOGRAPHIC_INTEGRITY_VERIFIED"

    # 2. Tampered signature
    env_tampered = dict(env)
    env_tampered["signature"] = "FORGED_SIGNATURE_0x123"
    env_tampered["nonce"] = f"nonce_tampered_{uuid.uuid4().hex[:6]}"
    sub, valid, algo, factors = CryptoEngine.evaluate("DRONE_REROUTE", env_tampered, now)
    assert valid is False
    assert sub >= 90.0
    assert factors[0].factor == "CRYPTOGRAPHIC_SPOOFING_DETECTED"

    # 3. Anti-Replay Detection: Re-using the same nonce
    sub_rep, valid_rep, algo, factors_rep = CryptoEngine.evaluate("DRONE_REROUTE", env, now)
    assert valid_rep is False
    assert sub_rep >= 95.0
    assert factors_rep[0].factor == "CRYPTOGRAPHIC_REPLAY_DETECTED"

    # 4. Sensitive command without signature
    sub_unsig, valid_unsig, _, factors_unsig = CryptoEngine.evaluate("FIRE_ORDER", {}, now)
    assert valid_unsig is False
    assert sub_unsig == 100.0


def test_recon_engine_mitre_mapping():
    # 1. Port scan pattern -> MITRE T1595.001
    sub, factors = ReconEngine.evaluate("PORT_SCAN", "Gateway-1", {})
    assert sub >= 75.0
    assert "T1595_001" in factors[0].factor

    # 2. Password brute force -> MITRE T1110.001
    sub, factors = ReconEngine.evaluate("AUTH_BRUTE_FORCE", "Auth-Proxy", {})
    assert sub >= 85.0
    assert "T1110_001" in factors[0].factor

    # 3. Benign telemetry -> 0 subscore
    sub, factors = ReconEngine.evaluate("TELEMETRY_BEACON", "Telemetry-Bus", {})
    assert sub == 0.0
    assert factors[0].factor == "BENIGN_EXTERNAL_PATTERN"


def test_circuit_breaker_engine():
    src_ip = f"192.0.2.{uuid.uuid4().int % 200 + 1}"
    CircuitBreakerEngine.reset_state(src_ip)
    now = datetime.now(timezone.utc)

    # 1. Single request -> CLOSED
    sub, tripped, state, factors = CircuitBreakerEngine.evaluate(src_ip, now)
    assert tripped is False
    assert state == "CLOSED"
    assert sub == 0.0

    # 2. Simulate flood of 16 burst requests
    for i in range(15):
        CircuitBreakerEngine.evaluate(src_ip, now + timedelta(seconds=0.1 * i))

    sub_burst, tripped_burst, state_burst, factors_burst = CircuitBreakerEngine.evaluate(
        src_ip, now + timedelta(seconds=2)
    )
    assert tripped_burst is True
    assert state_burst == "OPEN"
    assert sub_burst == 100.0
    assert factors_burst[0].factor in ["CIRCUIT_BREAKER_TRIPPED", "CIRCUIT_BREAKER_ACTIVE_QUARANTINE"]


def test_praharak_risk_engine():
    now = datetime.now(timezone.utc)
    ts_str = now.isoformat()
    nonce = f"nonce_risk_{uuid.uuid4().hex[:6]}"
    sig = CryptoEngine.generate_hmac_signature(b"test_payload", ts_str, nonce)

    # Valid external beacon
    score, tier, disp, valid, algo, tripped, factors = PraharakRiskEngine.evaluate(
        source_ip="10.0.0.1",
        source_asn="AS13335",
        target_service="Sensor-Gateway",
        command_type="SENSOR_BEACON",
        raw_envelope={"payload": "test_payload", "timestamp": ts_str, "nonce": nonce, "algorithm": "HMAC_SHA256", "signature": sig},
        current_time=now,
    )
    assert score <= 30.0
    assert tier == "LOW"
    assert disp == "ALLOWED"
    assert valid is True


# ==================== API & INTEGRATION TESTS ====================

@pytest.mark.asyncio
async def test_signal_ingestion_api(client_with_db):
    ac, session_maker = client_with_db

    now = datetime.now(timezone.utc)
    ts_str = now.isoformat()
    nonce = f"nonce_api_{uuid.uuid4().hex[:6]}"
    sig = CryptoEngine.generate_hmac_signature(b"status_report", ts_str, nonce)

    payload = {
        "signal_identifier": "SIG-TEST-001",
        "source_ip": "10.0.0.2",
        "source_asn": "AS13335",
        "target_service": "Command-Gateway",
        "command_type": "STATUS_REPORT",
        "raw_envelope": {
            "payload": "status_report",
            "timestamp": ts_str,
            "nonce": nonce,
            "algorithm": "HMAC_SHA256",
            "signature": sig,
        },
    }

    res = await ac.post("/api/v1/praharak/signals", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["signal_identifier"] == "SIG-TEST-001"
    assert data["risk_tier"] == "LOW"
    assert data["disposition"] == "ALLOWED"
    assert len(data["audit_hash"]) == 64


@pytest.mark.asyncio
async def test_praharak_demo_scenarios(client_with_db):
    ac, session_maker = client_with_db

    # 1. Normal Telemetry Scenario
    res1 = await ac.post("/api/v1/praharak/scenarios/trigger", json={"scenario": "normal_telemetry"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["risk_tier"] == "LOW"
    assert data1["disposition"] == "ALLOWED"
    assert data1["circuit_breaker_tripped"] is False

    # 2. Spoofed Tactical Command Scenario
    res2 = await ac.post("/api/v1/praharak/scenarios/trigger", json={"scenario": "spoofed_command"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["risk_tier"] == "CRITICAL"
    assert data2["disposition"] == "BLOCKED"

    # 3. DDoS Flood Scenario
    res3 = await ac.post("/api/v1/praharak/scenarios/trigger", json={"scenario": "ddos_flood"})
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["circuit_breaker_tripped"] is True

    # 4. Hybrid Coordinated Attack Scenario (The Grand Differentiator!)
    res4 = await ac.post("/api/v1/praharak/scenarios/trigger", json={"scenario": "hybrid_coordinated_attack"})
    assert res4.status_code == 200
    data4 = res4.json()
    assert data4["risk_tier"] == "CRITICAL"
    assert data4["cross_domain_incident_id"] is not None

    # Verify incident endpoint returns the cross-domain incident
    res_inc = await ac.get("/api/v1/praharak/incidents")
    assert res_inc.status_code == 200
    incidents = res_inc.json()
    assert len(incidents) >= 1
    assert incidents[0]["attack_pattern"] == "HYBRID_RECON_CREDENTIAL_ABUSE"
    assert incidents[0]["unified_risk_score"] >= 85.0
