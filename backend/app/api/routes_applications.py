from fastapi import APIRouter

router = APIRouter()


@router.post("")
async def create_application():
    return {"message": "Application endpoint - to be implemented"}


@router.get("/{application_id}")
async def get_application(application_id: str):
    return {"application_id": application_id, "status": "pending"}
