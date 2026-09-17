from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(db: AsyncSession = Depends(get_db)):
    """Verifies service health and database connectivity."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected ({str(e)})"

    return HealthResponse(
        status="healthy" if "connected" in db_status else "degraded",
        database=db_status,
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
    )
