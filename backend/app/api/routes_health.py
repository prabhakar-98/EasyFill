from fastapi import APIRouter

from app.config.settings import settings
from app.logging import get_logger

router = APIRouter()
logger = get_logger("health")


@router.get("/health")
async def health_check():
    logger.debug("health_check", status="healthy")
    return {
        "status": "healthy",
        "app": settings.app_name,
        "env": settings.app_env,
    }
