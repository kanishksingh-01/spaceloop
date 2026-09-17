import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.core.seeds import seed_initial_data
from app.main import app


@pytest.fixture
async def client_with_seeded_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    import app.core.seeds as seeds_module
    import app.core.database as db_module
    original_session = seeds_module.AsyncSessionLocal

    seeds_module.AsyncSessionLocal = session_maker
    db_module.AsyncSessionLocal = session_maker

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[db_module.get_db] = override_get_db

    await seed_initial_data()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, session_maker

    app.dependency_overrides.clear()
    seeds_module.AsyncSessionLocal = original_session
    db_module.AsyncSessionLocal = original_session
    await engine.dispose()


@pytest.mark.asyncio
async def test_policy_management_api(client_with_seeded_db):
    ac, _ = client_with_seeded_db

    # 1. Retrieve all policies
    res = await ac.get("/api/v1/policies")
    assert res.status_code == 200
    data = res.json()
    assert "active_weights" in data
    assert "active_thresholds" in data
    assert data["active_weights"]["WEIGHT_IDENTITY"] == 0.23
    assert data["active_weights"]["WEIGHT_ANOMALY"] == 0.08
    assert data["active_thresholds"]["THRESHOLD_CRITICAL"] == 81.0

    # 2. Update a policy weight
    update_res = await ac.put("/api/v1/policies/WEIGHT_ANOMALY", json={
        "value": 0.15,
        "justification": "Calibrated ML anomaly weighting for high-sensitivity operations",
    })
    assert update_res.status_code == 200
    up_data = update_res.json()
    assert up_data["key"] == "WEIGHT_ANOMALY"
    assert up_data["value"] == 0.15

    # 3. Verify updated policy is reflected
    verify_res = await ac.get("/api/v1/policies")
    assert verify_res.status_code == 200
    assert verify_res.json()["active_weights"]["WEIGHT_ANOMALY"] == 0.15

    # 4. Verify invalid weight is rejected
    bad_res = await ac.put("/api/v1/policies/WEIGHT_ANOMALY", json={
        "value": 1.5,
        "justification": "Invalid value > 1.0",
    })
    assert bad_res.status_code == 400


@pytest.mark.asyncio
async def test_device_trust_management_api(client_with_seeded_db):
    ac, _ = client_with_seeded_db

    # 1. List devices
    devices_res = await ac.get("/api/v1/devices")
    assert devices_res.status_code == 200
    devices = devices_res.json()
    assert len(devices) >= 5
    target_dev = next(d for d in devices if d["device_identifier"] == "DEV-101")
    assert target_dev["trust_level"] == "TRUSTED"

    # 2. Revoke device trust
    patch_res = await ac.patch(f"/api/v1/devices/{target_dev['id']}/trust", json={
        "trust_level": "REVOKED",
        "justification": "Endpoint suspected compromised in physical theft incident",
    })
    assert patch_res.status_code == 200
    updated_dev = patch_res.json()
    assert updated_dev["trust_level"] == "REVOKED"
    assert updated_dev["status"] == "SUSPENDED"

    # 3. Verify Audit Log was recorded
    audit_res = await ac.get("/api/v1/audit/logs")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    trust_logs = [l for l in logs if l["action"] == "device:update_trust"]
    assert len(trust_logs) >= 1
    assert "REVOKED" in str(trust_logs[0]["details"])
