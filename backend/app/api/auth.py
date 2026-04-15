import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import User
from app.models.enums import UserRole
from app.auth.dependencies import create_access_token
from app.auth.schemas import AuthRegisterRequest, AuthTokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse)
async def register_or_login(data: AuthRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user or return token for existing user (simplified OTP-less flow for Phase 1)."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=uuid.uuid4(),
            email=data.email,
            name=data.name or data.email.split("@")[0],
            auth_provider="email",
            role=UserRole.citizen,
        )
        db.add(user)
        await db.flush()

    token = create_access_token(str(user.id), user.role.value)
    return AuthTokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role.value,
    )


@router.post("/anonymous", response_model=AuthTokenResponse)
async def get_anonymous_token(db: AsyncSession = Depends(get_db)):
    """Create an anonymous user session for rate-limited reporting."""
    user = User(
        id=uuid.uuid4(),
        name="Anonymous",
        auth_provider="anonymous",
        is_anonymous_allowed=True,
        role=UserRole.citizen,
    )
    db.add(user)
    await db.flush()

    token = create_access_token(str(user.id), user.role.value)
    return AuthTokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role.value,
    )
