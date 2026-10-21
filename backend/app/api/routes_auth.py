import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.models.user import User
from app.database.models.user_profile import UserProfile
from app.security import hash_password, verify_password, create_access_token, get_current_user
from app.logging import get_logger

router = APIRouter()
logger = get_logger("routes_auth")


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = None
    last_name: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email address")
        return v.lower().strip()


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v):
        return v.lower().strip()


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str | None = None
    last_name: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        status="ACTIVE",
        auth_provider="email",
    )
    db.add(user)
    await db.flush()

    profile = UserProfile(
        user_id=user.id,
        first_name=request.first_name,
        last_name=request.last_name,
    )
    db.add(profile)
    await db.commit()

    token = create_access_token(user.id, user.email)

    logger.info("user_registered", user_id=str(user.id), email=user.email)

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=request.first_name,
            last_name=request.last_name,
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(user.id, user.email)

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()

    logger.info("user_logged_in", user_id=str(user.id), email=user.email)

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            first_name=profile.first_name if profile else None,
            last_name=profile.last_name if profile else None,
        ),
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "status": current_user.status,
    }
