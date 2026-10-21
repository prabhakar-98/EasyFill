from datetime import datetime

from app.database import connection as db_connection
from app.database.models.approval import Approval
from app.logging import get_logger
from app.workflows.events import emit_event
from app.workflows.state import ResolvedField, WorkflowState

logger = get_logger("workflow.hitl")


async def hitl_node(state: WorkflowState) -> dict:
    confident: list[ResolvedField] = state["confident_fields"]
    uncertain: list[ResolvedField] = state["uncertain_fields"]

    final: list[ResolvedField] = []
    final.extend(confident)
    final.extend(uncertain)

    final.sort(key=lambda f: f["index"])

    review_count = len(uncertain)

    if review_count > 0 and db_connection.async_session_factory:
        task_id = state.get("task_id", "")
        workflow_id = state.get("workflow_id", "")
        user_id = state.get("user_id", "")

        if task_id and workflow_id and user_id:
            now = datetime.utcnow()
            async with db_connection.async_session_factory() as session:
                for field in uncertain:
                    session.add(Approval(
                        task_id=task_id,
                        workflow_id=workflow_id,
                        user_id=user_id,
                        action_type="field_review",
                        status="PENDING",
                        payload={
                            "label": field["label"],
                            "value": field.get("value"),
                            "confidence": field.get("confidence", 0),
                            "review_reason": field.get("review_reason"),
                            "canonical_key": field.get("canonical_key"),
                            "field_type": field.get("type"),
                            "options": field.get("options", []),
                        },
                        requested_at=now,
                    ))
                await session.commit()

    task_id_val = state.get("task_id", "")
    workflow_id_val = state.get("workflow_id", "")

    for field in uncertain:
        await emit_event(
            workflow_id=workflow_id_val,
            task_id=task_id_val,
            event_type="approval_created",
            data={
                "label": field["label"],
                "reason": field.get("review_reason"),
            },
        )

    await emit_event(
        workflow_id=workflow_id_val,
        task_id=task_id_val,
        event_type="hitl_complete",
        data={"review_count": review_count, "total": len(final)},
    )

    logger.info(
        "hitl_merge",
        total=len(final),
        confident=len(confident),
        uncertain=review_count,
        needs_review=review_count,
        review_fields=[
            {
                "label": f["label"],
                "value": f["value"] if isinstance(f["value"], list) else (f["value"][:50] if f["value"] else None),
                "reason": f.get("review_reason"),
            }
            for f in uncertain
        ],
    )

    return {
        "final_fields": final,
        "status": "WAITING_FOR_HUMAN" if review_count > 0 else "STORING_RESULT",
        "current_node": "hitl",
        "events": [
            {
                "type": "hitl_complete",
                "review_count": review_count,
                "total": len(final),
            }
        ],
    }
