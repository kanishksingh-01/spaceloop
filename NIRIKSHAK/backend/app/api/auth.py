from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, decode_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
security_scheme = HTTPBearer(auto_error=False)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates using seeded credentials (e.g. analyst_sarah / analyst123)."""
    stmt = select(User).where(User.username == payload.username).options(selectinload(User.role))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or inactive",
        )

    role_name = user.role.name if user.role else "USER"
    access_token = create_access_token(
        subject=user.username,
        role=role_name,
        user_id=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            external_identifier=user.external_identifier,
            username=user.username,
            role=role_name,
            department=user.department,
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves current user profile from bearer token."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")

    payload = decode_access_token(credentials.credentials)
    if not payload or "user_id" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    stmt = select(User).where(User.id == payload["user_id"]).options(selectinload(User.role))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(
        id=user.id,
        external_identifier=user.external_identifier,
        username=user.username,
        role=user.role.name if user.role else "USER",
        department=user.department,
    )
