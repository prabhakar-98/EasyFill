from datetime import datetime

from app.database import connection as db_connection
from app.database.models.task import Task
from app.database.models.workflow import Workflow
from app.logging import get_logger
from app.workflows.events import emit_event
from app.workflows.state import WorkflowState

logger = get_logger("workflow.create_task")


async def create_task_node(state: WorkflowState) -> dict:
    if not db_connection.async_session_factory:
        raise RuntimeError("Database not initialized")

    now = datetime.utcnow()

    async with db_connection.async_session_factory() as session:
        task = Task(
            user_id=state["user_id"],
            type="autofill",
            status="RUNNING",
            title=state.get("form_title") or (f"Autofill: {state['url'][:100]}" if state.get("url") else "Autofill"),
            url=state.get("url", ""),
            input={
                "url": state.get("url", ""),
                "form_title": state.get("form_title", ""),
                "form_description": state.get("form_description", ""),
                "fields": state["fields"],
            },
        )
        session.add(task)
        await session.flush()

        workflow = Workflow(
            task_id=task.id,
            workflow_type="autofill",
            status="RUNNING",
            current_node="create_task",
            started_at=now,
        )
        session.add(workflow)
        await session.commit()

        task_id = str(task.id)
        workflow_id = str(workflow.id)

    logger.info(
        "task_created",
        task_id=task_id,
        workflow_id=workflow_id,
        user_id=state["user_id"],
        field_count=len(state["fields"]),
        fields=[
            {"index": f["index"], "label": f["label"], "type": f["type"]}
            for f in state["fields"]
        ],
    )

    await emit_event(
        workflow_id=workflow_id,
        task_id=task_id,
        event_type="task_created",
        data={"field_count": len(state["fields"]), "url": state.get("url", "")},
    )

    return {
        "task_id": task_id,
        "workflow_id": workflow_id,
        "status": "RUNNING",
        "current_node": "create_task",
        "events": [
            {
                "type": "task_created",
                "task_id": task_id,
                "workflow_id": workflow_id,
                "field_count": len(state["fields"]),
            }
        ],
    }
