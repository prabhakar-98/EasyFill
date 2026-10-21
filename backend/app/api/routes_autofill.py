from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AutofillRequest, AutofillResponse, FieldInfo
from app.database.connection import get_db
from app.database.models.user import User
from app.database.models.user_profile import UserProfile
from app.security import get_current_user
from app.logging import get_logger

router = APIRouter()
logger = get_logger("routes_autofill")


def build_profile_dict(user: User, profile: UserProfile | None) -> dict[str, str]:
    d: dict[str, str] = {}
    if not profile:
        return d

    if profile.first_name:
        d["first name"] = profile.first_name
    if profile.last_name:
        d["last name"] = profile.last_name
    if profile.first_name and profile.last_name:
        full = f"{profile.first_name} {profile.last_name}"
        d["name"] = full
        d["full name"] = full
    d["email"] = user.email
    d["email address"] = user.email
    if profile.phone:
        d["phone"] = profile.phone
        d["phone number"] = profile.phone
        d["mobile"] = profile.phone
    if profile.location:
        d["location"] = profile.location
        d["city"] = profile.location
        d["address"] = profile.location
    if profile.headline:
        d["headline"] = profile.headline
        d["current role"] = profile.headline
        d["job title"] = profile.headline
    if profile.bio:
        d["bio"] = profile.bio

    pd = profile.professional_data or {}

    if pd.get("skills"):
        skills = pd["skills"]
        d["skills"] = ", ".join(skills) if isinstance(skills, list) else skills

    if pd.get("education") and len(pd["education"]) > 0:
        edu = pd["education"][0]
        if edu.get("institution"):
            d["college"] = edu["institution"]
            d["university"] = edu["institution"]
        if edu.get("degree"):
            d["degree"] = edu["degree"]
        if edu.get("field_of_study"):
            d["major"] = edu["field_of_study"]
            d["branch"] = edu["field_of_study"]
        if edu.get("gpa"):
            d["gpa"] = edu["gpa"]
            d["cgpa"] = edu["gpa"]
        if edu.get("graduation_year"):
            d["graduation year"] = edu["graduation_year"]
            d["year of graduation"] = edu["graduation_year"]

    if pd.get("work_experience") and len(pd["work_experience"]) > 0:
        job = pd["work_experience"][0]
        if job.get("company"):
            d["company"] = job["company"]
            d["current company"] = job["company"]
        if job.get("title"):
            d["current role"] = job["title"]
            d["job title"] = job["title"]
        if job.get("years"):
            d["experience"] = job["years"]
            d["years of experience"] = job["years"]

    links = pd.get("links", {})
    if links.get("linkedin"):
        d["linkedin"] = links["linkedin"]
        d["linkedin url"] = links["linkedin"]
    if links.get("github"):
        d["github"] = links["github"]
        d["github url"] = links["github"]
    if links.get("website"):
        d["website"] = links["website"]
    if links.get("portfolio"):
        d["portfolio"] = links["portfolio"]

    if pd.get("salary_expectation"):
        d["expected salary"] = pd["salary_expectation"]
        d["salary expectation"] = pd["salary_expectation"]
    if pd.get("notice_period"):
        d["notice period"] = pd["notice_period"]
    if pd.get("availability"):
        d["availability"] = pd["availability"]
    if pd.get("gender"):
        d["gender"] = pd["gender"]

    return {k: v for k, v in d.items() if v}


@router.post("/autofill", response_model=AutofillResponse)
async def autofill(
    request: AutofillRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    profile_dict = build_profile_dict(current_user, profile)

    values = {}

    for field in request.fields:
        label_lower = field.label.lower().strip()

        matched_value = profile_dict.get(label_lower)

        if not matched_value:
            for key, val in profile_dict.items():
                if key in label_lower or label_lower in key:
                    matched_value = val
                    break

        if matched_value and field.type in ("multiple_choice", "dropdown") and field.options:
            best = None
            for opt in field.options:
                if matched_value.lower() in opt.lower() or opt.lower() in matched_value.lower():
                    best = opt
                    break
            if best:
                matched_value = best
            else:
                matched_value = None

        if matched_value:
            values[field.label] = matched_value

    logger.info(
        "autofill_request",
        user_id=str(current_user.id),
        url=request.url,
        total_fields=len(request.fields),
        matched_fields=len(values),
    )

    return AutofillResponse(
        values=values,
        matched=len(values),
        total=len(request.fields),
    )
