import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.database import Base, get_db
from app.core.seeds import seed_initial_data
from app.models.case import SecurityCase
from app.models.event import AccessEvent
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client_with_db():
    """Sets up an in-memory SQLite database populated with seeds and returns an AsyncClient."""
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Seed data
    import app.core.seeds as seeds_module
    original_session = seeds_module.AsyncSessionLocal
    seeds_module.AsyncSessionLocal = async_session

    await seed_initial_data()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, async_session

    app.dependency_overrides.clear()
    seeds_module.AsyncSessionLocal = original_session
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_event_ingestion_and_explanation(client_with_db):
    ac, session_maker = client_with_db

    # Ingest a custom event
    payload = {
        "event_id": "evt_test_custom_001",
        "user_identifier": "USER-001",
        "device_identifier": "DEV-101",
        "resource_identifier": "Operational Repository A",
        "action": "READ",
        "data_volume": 5000000,
        "source_context": {"mfa_verified": True, "corporate_network": True},
    }

    res = await ac.post("/api/v1/events", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["event_id"] == "evt_test_custom_001"
    assert "total_score" in data
    assert "risk_level" in data
    internal_id = data["internal_id"]

    # Retrieve explanation
    exp_res = await ac.get(f"/api/v1/events/{internal_id}/explanation")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert exp_data["event_id"] == internal_id
    assert len(exp_data["factors"]) > 0
    assert "contribution" in exp_data["factors"][0]


@pytest.mark.asyncio
async def test_scenario_triggers_and_auto_case_creation(client_with_db):
    ac, session_maker = client_with_db

    # 1. Trigger Normal Scenario -> LOW Risk, No Case
    norm_res = await ac.post("/api/v1/scenarios/trigger", json={"scenario": "normal"})
    assert norm_res.status_code == 200
    norm_data = norm_res.json()
    assert norm_data["risk_level"] == "LOW"
    assert norm_data["case_created"] is False
    assert norm_data["case_id"] is None

    # 2. Trigger Off-Hours Scenario -> HIGH Risk, Case Created
    off_res = await ac.post("/api/v1/scenarios/trigger", json={"scenario": "off_hours"})
    assert off_res.status_code == 200
    off_data = off_res.json()
    assert off_data["risk_level"] in ["HIGH", "CRITICAL"]
    assert off_data["case_created"] is True
    assert off_data["case_id"] is not None

    # 3. Trigger Exfiltration Scenario -> CRITICAL Risk, Case Created
    exfil_res = await ac.post("/api/v1/scenarios/trigger", json={"scenario": "exfiltration"})
    assert exfil_res.status_code == 200
    exfil_data = exfil_res.json()
    assert exfil_data["risk_level"] == "CRITICAL"
    assert exfil_data["case_created"] is True
    assert exfil_data["case_id"] is not None

    # 4. Verify Case Record in Database
    async with session_maker() as session:
        cases = (await session.execute(select(SecurityCase))).scalars().all()
        assert len(cases) == 2  # 1 from off_hours + 1 from exfiltration
        statuses = [c.status for c in cases]
        assert all(s == "OPEN" for s in statuses)

    # 5. Verify Event List Endpoint returns all ingested events
    list_res = await ac.get("/api/v1/events")
    assert list_res.status_code == 200
    events_list = list_res.json()
    assert len(events_list) >= 3
    # Check that case_id is attached to high risk events
    exfil_event = next(e for e in events_list if e["event_id"] == exfil_data["event_id"])
    assert exfil_event["case_id"] == exfil_data["case_id"]
    assert exfil_event["risk_level"] == "CRITICAL"
