import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.core.database import Base, get_db
from app.core.seeds import seed_initial_data
from app.models.user import User, Role
from app.models.resource import ResourceClassification, Resource
from app.models.device import Device
from app.models.baseline import BehaviorBaseline
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_session():
    """Creates an isolated in-memory test database session."""
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_schema_creation_and_seed_fixtures(test_session: AsyncSession):
    """Verifies that Base.metadata.create_all() works and seeds load cleanly."""
    # Run seed function using monkeypatched session
    import app.core.seeds as seeds_module
    original_session = seeds_module.AsyncSessionLocal
    seeds_module.AsyncSessionLocal = lambda: test_session

    try:
        await seed_initial_data()

        # 1. Verify Roles
        roles = (await test_session.execute(select(Role))).scalars().all()
        role_names = [r.name for r in roles]
        assert "ANALYST" in role_names
        assert "ADMIN" in role_names
        assert "USER" in role_names

        # 2. Verify Seeded Demo Accounts
        users = (await test_session.execute(select(User))).scalars().all()
        usernames = [u.username for u in users]
        assert "analyst_sarah" in usernames
        assert "admin_vikram" in usernames
        assert "user_001" in usernames

        # 3. Verify Classifications
        classifications = (await test_session.execute(select(ResourceClassification))).scalars().all()
        levels = [c.level for c in classifications]
        assert "CRITICAL" in levels
        assert "CONFIDENTIAL" in levels

        # 4. Verify Resources
        resources = (await test_session.execute(select(Resource))).scalars().all()
        repo_names = [r.name for r in resources]
        assert "Operational Repository A" in repo_names
        assert "Engineering Repository B" in repo_names

        # 5. Verify Devices
        devices = (await test_session.execute(select(Device))).scalars().all()
        dev_ids = [d.device_identifier for d in devices]
        assert "DEV-101" in dev_ids
        assert "DEV-999" in dev_ids

        # 6. Verify Baselines
        baselines = (await test_session.execute(select(BehaviorBaseline))).scalars().all()
        assert len(baselines) == 10

    finally:
        seeds_module.AsyncSessionLocal = original_session


@pytest.mark.asyncio
async def test_health_and_auth_endpoints():
    """Tests the /health and /auth/login endpoints using AsyncClient."""
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

    try:
        await seed_initial_data()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Test Health endpoint
            health_res = await ac.get("/api/v1/health")
            assert health_res.status_code == 200
            data = health_res.json()
            assert data["status"] == "healthy"
            assert data["database"] == "connected"

            # 2. Test Login with seeded credentials
            login_res = await ac.post("/api/v1/auth/login", json={
                "username": "analyst_sarah",
                "password": "analyst123"
            })
            assert login_res.status_code == 200
            token_data = login_res.json()
            assert "access_token" in token_data
            assert token_data["user"]["username"] == "analyst_sarah"
            assert token_data["user"]["role"] == "ANALYST"

            # 3. Test Invalid password rejection
            bad_login = await ac.post("/api/v1/auth/login", json={
                "username": "analyst_sarah",
                "password": "wrong_password"
            })
            assert bad_login.status_code == 401

    finally:
        app.dependency_overrides.clear()
        seeds_module.AsyncSessionLocal = original_session
        await test_engine.dispose()
