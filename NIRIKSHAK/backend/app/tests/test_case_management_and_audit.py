import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.database import Base, get_db
from app.core.seeds import seed_initial_data
from app.models.case import SecurityCase
from app.models.audit import AuditLog
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def case_test_client():
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
async def test_case_lifecycle_and_audit_logging(case_test_client):
    ac, session_maker = case_test_client

    # 1. Trigger Exfiltration scenario to create a CRITICAL case
    trigger_res = await ac.post("/api/v1/scenarios/trigger", json={"scenario": "exfiltration"})
    assert trigger_res.status_code == 200
    trig_data = trigger_res.json()
    case_id = trig_data["case_id"]
    assert case_id is not None

    # 2. List cases and verify the new case is listed
    cases_res = await ac.get("/api/v1/cases")
    assert cases_res.status_code == 200
    cases_list = cases_res.json()
    assert len(cases_list) >= 1
    target_case = next(c for c in cases_list if c["id"] == case_id)
    assert target_case["status"] == "OPEN"
    assert target_case["severity"] == "CRITICAL"

    # 3. Retrieve Case Detail
    detail_res = await ac.get(f"/api/v1/cases/{case_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == case_id
    assert len(detail_data["factors"]) > 0
    assert detail_data["status"] == "OPEN"

    # 4. Review Case: Invalid Action Rejection
    bad_action_res = await ac.post(f"/api/v1/cases/{case_id}/review", json={
        "action": "INVALID_ACTION",
        "justification": "This should fail validation."
    })
    assert bad_action_res.status_code == 400

    # 5. Review Case: ESCALATE with Valid Justification
    escalate_res = await ac.post(f"/api/v1/cases/{case_id}/review", json={
        "action": "ESCALATE",
        "justification": "Observed 2.5 GB download from unmanaged DEV-999 outside shift hours. Escalated to tier 2 for immediate identity verification."
    })
    assert escalate_res.status_code == 200
    review_data = escalate_res.json()
    assert review_data["status"] == "ESCALATED"
    assert review_data["reviewed_by"] == "analyst_sarah"
    assert "audit_log_id" in review_data

    # 6. Verify Case status updated in DB
    async with session_maker() as session:
        c_db = (await session.execute(select(SecurityCase).where(SecurityCase.id == case_id))).scalar_one()
        assert c_db.status == "ESCALATED"

        # Verify Audit Log entry created in DB
        audit_entry = (await session.execute(select(AuditLog).where(AuditLog.target_id == case_id))).scalar_one()
        assert audit_entry.action == "case:escalate"
        assert audit_entry.actor_username == "analyst_sarah"
        assert "unmanaged DEV-999" in audit_entry.justification

    # 7. Verify Audit Logs API returns the record
    audit_api_res = await ac.get("/api/v1/audit/logs")
    assert audit_api_res.status_code == 200
    audit_list = audit_api_res.json()
    assert len(audit_list) >= 1
    assert any(a["target_id"] == case_id for a in audit_list)
