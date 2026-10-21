from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.models.user import User
from app.database.models.user_profile import UserProfile
from app.security import get_current_user
from app.logging import get_logger
from app.services.indexing import index_user_profile

router = APIRouter()
logger = get_logger("routes_profile")


class Education(BaseModel):
    institution: str = ""
    degree: str = ""
    field_of_study: str | None = None
    gpa: str | None = None
    graduation_year: str | None = None


class WorkExperience(BaseModel):
    company: str = ""
    title: str = ""
    years: str | None = None
    current: bool = False


class Links(BaseModel):
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None
    portfolio: str | None = None


class ProfessionalData(BaseModel):
    skills: list[str] = []
    education: list[Education] = []
    work_experience: list[WorkExperience] = []
    links: Links | None = None
    salary_expectation: str | None = None
    notice_period: str | None = None
    availability: str | None = None
    gender: str | None = None


class ProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    bio: str | None = None
    professional_data: ProfessionalData | None = None


class ProfileResponse(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    bio: str | None = None
    professional_data: dict | None = None


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return ProfileResponse()

    return ProfileResponse(
        first_name=profile.first_name,
        last_name=profile.last_name,
        phone=profile.phone,
        location=profile.location,
        headline=profile.headline,
        bio=profile.bio,
        professional_data=profile.professional_data,
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    data = request.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "professional_data" and value is not None:
            setattr(profile, key, value if isinstance(value, dict) else value.model_dump())
        else:
            setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)

    try:
        await index_user_profile(str(current_user.id))
    except Exception as e:
        logger.warning("profile_index_failed", user_id=str(current_user.id), error=str(e))

    logger.info("profile_updated", user_id=str(current_user.id))

    return ProfileResponse(
        first_name=profile.first_name,
        last_name=profile.last_name,
        phone=profile.phone,
        location=profile.location,
        headline=profile.headline,
        bio=profile.bio,
        professional_data=profile.professional_data,
    )
