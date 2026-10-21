from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.schemas import ApprovalActionRequest, ApprovalResponse
from app.database import connection as db_connection
from app.database.models.approval import Approval
from app.database.models.personalized_memory import PersonalizedMemory
from app.database.models.user import User
from app.logging import get_logger
from app.security import get_current_user
from app.services.indexing import smart_index_memory
from app.workflows.events import emit_event

router = APIRouter()
logger = get_logger("routes_approval")


@router.get("/approvals", response_model=list[ApprovalResponse])
async def list_approvals(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    if not db_connection.async_session_factory:
        raise HTTPException(status_code=500, detail="Database not initialized")

    async with db_connection.async_session_factory() as session:
        result = await session.execute(
            select(Approval).where(
                Approval.task_id == task_id,
                Approval.user_id == current_user.id,
                Approval.status == "PENDING",
            )
        )
        approvals = result.scalars().all()

        return [
            ApprovalResponse(
                id=str(a.id),
                label=a.payload.get("label", ""),
                value=a.payload.get("value"),
                confidence=a.payload.get("confidence", 0),
                reason=a.payload.get("review_reason"),
                status=a.status,
            )
            for a in approvals
        ]


@router.post("/approvals/{approval_id}/respond")
async def respond_to_approval(
    approval_id: str,
    request: ApprovalActionRequest,
    current_user: User = Depends(get_current_user),
):
    if not db_connection.async_session_factory:
        raise HTTPException(status_code=500, detail="Database not initialized")

    async with db_connection.async_session_factory() as session:
        result = await session.execute(
            select(Approval).where(
                Approval.id == approval_id,
                Approval.user_id == current_user.id,
            )
        )
        approval = result.scalar_one_or_none()
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        if approval.status != "PENDING":
            raise HTTPException(status_code=400, detail="Approval already responded")

        now = datetime.utcnow()

        if request.action == "approve":
            approval.status = "APPROVED"
        elif request.action == "modify":
            approval.status = "MODIFIED"
            approval.payload = {**approval.payload, "value": request.value}
        elif request.action == "reject":
            approval.status = "REJECTED"

        approval.user_comment = request.comment
        approval.responded_at = now

        if request.action in ("approve", "modify"):
            field_key = approval.payload.get("label", "").lower().strip()
            value = request.value if request.action == "modify" else approval.payload.get("value")

            if field_key and value:
                source = "user_correction" if request.action == "modify" else "user_approved"
                existing = await session.execute(
                    select(PersonalizedMemory).where(
                        PersonalizedMemory.user_id == current_user.id,
                        PersonalizedMemory.key == field_key,
                    )
                )
                memory = existing.scalar_one_or_none()
                if memory:
                    memory.value = {"text": value}
                    memory.source = source
                    memory.confidence = 1.0
                    memory.confirmed_by_user = True
                else:
                    session.add(PersonalizedMemory(
                        user_id=current_user.id,
                        key=field_key,
                        value={"text": value},
                        source=source,
                        confidence=1.0,
                        confirmed_by_user=True,
                    ))

        await session.commit()

        if request.action in ("approve", "modify"):
            field_key = approval.payload.get("label", "").lower().strip()
            value = request.value if request.action == "modify" else approval.payload.get("value")
            if field_key and value:
                try:
                    await smart_index_memory(str(current_user.id), field_key, str(value))
                except Exception as e:
                    logger.warning("smart_index_failed", field=field_key, error=str(e))

        await emit_event(
            workflow_id=str(approval.workflow_id),
            task_id=str(approval.task_id),
            event_type="approval_responded",
            actor_type="user",
            actor_id=str(current_user.id),
            data={
                "label": approval.payload.get("label"),
                "action": request.action,
                "canonical_key": approval.payload.get("canonical_key"),
            },
        )

        logger.info(
            "approval_responded",
            approval_id=approval_id,
            action=request.action,
            label=approval.payload.get("label"),
            canonical_key=approval.payload.get("canonical_key"),
        )

        return {"status": approval.status, "action": request.action}
