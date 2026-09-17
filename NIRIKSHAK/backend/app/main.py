import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.seeds import seed_initial_data
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.events import router as events_router
from app.api.scenarios import router as scenarios_router
from app.api.cases import router as cases_router
from app.api.audit import router as audit_router
from app.api.policies import router as policies_router
from app.api.devices import router as devices_router
from app.api.praharak import router as praharak_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("nirikshak")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing DB initialization and seed loading."""
    logger.info("Starting NIRIKSHAK Backend (MVP)...")
    try:
        # Step 1: Create all tables via Base.metadata.create_all()
        await init_db()
        # Step 2: Seed synthetic initial fixtures
        await seed_initial_data()
        logger.info("NIRIKSHAK Backend startup complete.")
    except Exception as e:
        logger.error(f"Failed during startup initialization: {e}", exc_info=True)
        raise e

    yield

    logger.info("Shutting down NIRIKSHAK Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Contextual, Human-Supervised, Explainable Risk and Access Knowledge Framework (MVP)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(events_router, prefix=settings.API_PREFIX)
app.include_router(scenarios_router, prefix=settings.API_PREFIX)
app.include_router(cases_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
app.include_router(policies_router, prefix=settings.API_PREFIX)
app.include_router(devices_router, prefix=settings.API_PREFIX)
app.include_router(praharak_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {
        "framework": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
    }
