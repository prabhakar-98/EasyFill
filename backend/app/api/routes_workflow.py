from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from app.api.schemas import AutofillRequest, SubmitCaptureRequest, WorkflowResponse
from app.database import connection as db_connection
from app.database.models.personalized_memory import PersonalizedMemory
from app.database.models.task import Task
from app.database.models.user import User
from app.database.models.workflow import Workflow
from app.logging import get_logger
from app.security import get_current_user
from app.services.indexing import smart_index_memory
from app.workflows.autofill_graph import autofill_workflow
from app.workflows.events import emit_event

router = APIRouter()
logger = get_logger("routes_workflow")


@router.post("/workflow/start", response_model=WorkflowResponse)
async def start_workflow(
    raw_request: Request,
    request: AutofillRequest,
    current_user: User = Depends(get_current_user),
):
    raw_body = await raw_request.json()
    logger.info(
        "raw_request_body",
        user_id=str(current_user.id),
        body=raw_body,
    )

    initial_state = {
        "user_id": str(current_user.id),
        "task_id": "",
        "workflow_id": "",
        "url": request.url or "",
        "form_title": request.form_title or "",
        "form_description": request.form_description or "",
        "fields": [f.model_dump() for f in request.fields],
        "status": "PENDING",
        "mapped_fields": [],
        "resolved_fields": [],
        "confident_fields": [],
        "uncertain_fields": [],
        "final_fields": [],
        "values": {},
        "matched": 0,
        "total": len(request.fields),
        "events": [],
        "errors": [],
        "current_node": "",
    }

    logger.info(
        "workflow_request_received",
        user_id=str(current_user.id),
        url=request.url,
        form_title=request.form_title,
        form_description=request.form_description,
        field_count=len(request.fields),
        fields=[
            {
                "index": f.index,
                "label": f.label,
                "type": f.type,
                "required": f.required,
                "description": f.description,
                "options": f.options,
                "validation": f.validation,
            }
            for f in request.fields
        ],
    )

    try:
        result = await autofill_workflow.ainvoke(initial_state)

        # store_result sets values/matched, build needs_review from final_fields
        values = result.get("values", {})
        matched = result.get("matched", 0)

        needs_review: list[dict] = []
        for field in result.get("final_fields", []):
            if field.get("needs_review"):
                needs_review.append({
                    "label": field["label"],
                    "value": field.get("value"),
                    "confidence": field.get("confidence", 0),
                    "reason": field.get("review_reason"),
                })

        logger.info(
            "workflow_completed",
            task_id=result.get("task_id"),
            user_id=str(current_user.id),
            matched=matched,
            total=len(request.fields),
            filled_fields=list(values.keys()),
            needs_review_count=len(needs_review),
        )

        return WorkflowResponse(
            values=values,
            matched=matched,
            total=len(request.fields),
            task_id=result.get("task_id"),
            needs_review=needs_review if needs_review else None,
        )

    except Exception as e:
        logger.error(
            "workflow_failed",
            user_id=str(current_user.id),
            error=str(e),
        )
        return WorkflowResponse(
            values={},
            matched=0,
            total=len(request.fields),
        )


@router.post("/workflow/submit-capture")
async def submit_capture(
    request: SubmitCaptureRequest,
    current_user: User = Depends(get_current_user),
):
    if not db_connection.async_session_factory:
        raise HTTPException(status_code=500, detail="Database not initialized")

    async with db_connection.async_session_factory() as session:
        task_result = await session.execute(
            select(Task).where(
                Task.id == request.task_id,
                Task.user_id == current_user.id,
            )
        )
        task = task_result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        autofilled = task.result.get("values", {}) if task.result else {}
        corrections = 0
        confirmations = 0
        fields_to_index: list[tuple[str, str]] = []

        for label, submitted_value in request.final_values.items():
            autofilled_value = autofilled.get(label)
            field_key = label.lower().strip()

            submitted_str = str(submitted_value) if submitted_value else ""
            autofilled_str = str(autofilled_value) if autofilled_value else ""

            if not submitted_str:
                continue

            is_correction = autofilled_str and submitted_str != autofilled_str
            is_new = not autofilled_str

            if is_correction or is_new:
                source = "user_correction" if is_correction else "user_provided"
                existing = await session.execute(
                    select(PersonalizedMemory).where(
                        PersonalizedMemory.user_id == current_user.id,
                        PersonalizedMemory.key == field_key,
                    )
                )
                memory = existing.scalar_one_or_none()
                if memory:
                    memory.value = {"text": submitted_str}
                    memory.source = source
                    memory.confidence = 1.0
                    memory.confirmed_by_user = True
                else:
                    session.add(PersonalizedMemory(
                        user_id=current_user.id,
                        key=field_key,
                        value={"text": submitted_str},
                        source=source,
                        confidence=1.0,
                        confirmed_by_user=True,
                    ))
                fields_to_index.append((field_key, submitted_str))
                corrections += 1
            elif autofilled_str == submitted_str:
                existing = await session.execute(
                    select(PersonalizedMemory).where(
                        PersonalizedMemory.user_id == current_user.id,
                        PersonalizedMemory.key == field_key,
                    )
                )
                memory = existing.scalar_one_or_none()
                if memory and memory.confidence and memory.confidence < 1.0:
                    memory.confirmed_by_user = True
                    memory.confidence = 1.0
                    fields_to_index.append((field_key, autofilled_str))
                confirmations += 1

        await session.commit()

    user_id_str = str(current_user.id)
    for field_key, value in fields_to_index:
        try:
            await smart_index_memory(user_id_str, field_key, value)
        except Exception as e:
            logger.warning("smart_index_failed", field=field_key, error=str(e))

    # Emit audit event
    async with db_connection.async_session_factory() as session:
        wf_result = await session.execute(
            select(Workflow).where(Workflow.task_id == request.task_id)
        )
        wf = wf_result.scalar_one_or_none()
        if wf:
            await emit_event(
                workflow_id=str(wf.id),
                task_id=request.task_id,
                event_type="submit_captured",
                actor_type="user",
                actor_id=str(current_user.id),
                data={
                    "corrections": corrections,
                    "confirmations": confirmations,
                    "submitted_fields": len(request.final_values),
                },
            )

    logger.info(
        "submit_captured",
        task_id=request.task_id,
        user_id=str(current_user.id),
        submitted_fields=len(request.final_values),
        corrections=corrections,
        confirmations=confirmations,
    )

    return {
        "status": "captured",
        "corrections": corrections,
        "confirmations": confirmations,
    }
