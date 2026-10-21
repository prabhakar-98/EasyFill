from datetime import datetime

from sqlalchemy import select

from app.database import connection as db_connection
from app.database.models.task import Task
from app.database.models.workflow import Workflow
from app.logging import get_logger
from app.workflows.events import emit_event
from app.workflows.state import ResolvedField, WorkflowState

logger = get_logger("workflow.store_result")


async def store_result_node(state: WorkflowState) -> dict:
    final_fields: list[ResolvedField] = state["final_fields"]
    user_id = state["user_id"]

    values: dict[str, str | list[str]] = {}
    for field in final_fields:
        if field["value"]:
            values[field["label"]] = field["value"]

    matched = len(values)
    total = state["total"]

    task_id = state.get("task_id", "")
    workflow_id = state.get("workflow_id", "")

    if task_id and db_connection.async_session_factory:
        now = datetime.utcnow()
        async with db_connection.async_session_factory() as session:
            task_result = await session.execute(
                select(Task).where(Task.id == task_id)
            )
            task = task_result.scalar_one_or_none()
            if task:
                task.status = "COMPLETED"
                task.result = {"values": values, "matched": matched, "total": total}
                task.completed_at = now

            wf_result = await session.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = wf_result.scalar_one_or_none()
            if workflow:
                workflow.status = "COMPLETED"
                workflow.current_node = "store_result"
                workflow.completed_at = now

            await session.commit()

    await emit_event(
        workflow_id=workflow_id,
        task_id=task_id,
        event_type="result_stored",
        data={"matched": matched, "total": total},
    )

    logger.info(
        "result_stored",
        task_id=task_id,
        matched=matched,
        total=total,
        filled_labels=list(values.keys()),
    )

    return {
        "values": values,
        "matched": matched,
        "status": "COMPLETED",
        "current_node": "store_result",
        "events": [
            {
                "type": "result_stored",
                "matched": matched,
                "total": total,
            }
        ],
    }
