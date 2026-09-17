import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.core.seeds import seed_initial_data
from app.main import app


@pytest.fixture
async def sec_test_client():
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
        yield ac

    app.dependency_overrides.clear()
    seeds_module.AsyncSessionLocal = original_session
    db_module.AsyncSessionLocal = original_session
    await engine.dispose()


@pytest.mark.asyncio
async def test_sql_injection_resistance(sec_test_client):
    """Verifies that SQL injection payloads are neutralized by SQLAlchemy parameterization."""
    ac = sec_test_client

    # 1. SQL Injection attempt in event filter
    sqli_payload = "' OR '1'='1"
    res = await ac.get(f"/api/v1/events?user_identifier={sqli_payload}")
    assert res.status_code == 200
    # Parameterized query returns 0 matches rather than leaking all rows
    assert len(res.json()) == 0

    # 2. SQL Injection in case ID lookup
    res_case = await ac.get("/api/v1/cases/' OR 1=1--")
    assert res_case.status_code == 404


@pytest.mark.asyncio
async def test_terminal_command_injection_rejection(sec_test_client):
    """Verifies that OS shell commands are strictly rejected by policy API."""
    ac = sec_test_client

    dangerous_keys = [
        "WEIGHT_ID; rm -rf",
        "WEIGHT_`cat /etc/passwd`",
        "WEIGHT_$(whoami)",
        "|| sudo shutdown",
        "; whoami",
    ]

    for bad_key in dangerous_keys:
        res = await ac.put(f"/api/v1/policies/{bad_key}", json={"value": 0.5})
        # Must be safely rejected with 400 Bad Request or 404 Unrouted
        assert res.status_code in [400, 404]


@pytest.mark.asyncio
async def test_audit_log_immutability(sec_test_client):
    """Verifies that audit logs cannot be updated or deleted via API endpoints."""
    ac = sec_test_client

    # 1. Audit logs endpoint does not permit PUT, PATCH, or DELETE
    put_res = await ac.put("/api/v1/audit/logs", json={"action": "TAMPER"})
    assert put_res.status_code in [404, 405]

    delete_res = await ac.delete("/api/v1/audit/logs")
    assert delete_res.status_code in [404, 405]

    patch_res = await ac.patch("/api/v1/audit/logs/1", json={"details": "tampered"})
    assert patch_res.status_code in [404, 405]


@pytest.mark.asyncio
async def test_case_review_validation_guard(sec_test_client):
    """Verifies that arbitrary actions cannot be executed during case review."""
    ac = sec_test_client

    # Case review with malicious or illegal action verb
    res = await ac.post("/api/v1/cases/any-id/review", json={
        "action": "DROP_DATABASE",
        "justification": "Exploit attempt",
    })
    assert res.status_code == 400
    assert "Invalid review action" in res.json()["detail"]
