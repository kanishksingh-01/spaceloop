import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine connect args (e.g. SQLite vs PostgreSQL)
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

# Create Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.0 models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Creates all database tables on startup using Base.metadata.create_all()."""
    # Import all models to register them with Base.metadata before create_all
    import app.models  # noqa: F401

    logger.info("Initializing database schema with Base.metadata.create_all()...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if not is_sqlite:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE risk_scores ADD COLUMN IF NOT EXISTS anomaly_score FLOAT DEFAULT 0.0;"))
            await conn.execute(text("ALTER TABLE risk_scores ADD COLUMN IF NOT EXISTS correlation_score FLOAT DEFAULT 0.0;"))
    logger.info("Database schema successfully verified and created.")
