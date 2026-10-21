from app.database import connection as db_connection
from app.database.models.workflow_event import WorkflowEvent
from app.logging import get_logger

logger = get_logger("workflow.events")


async def emit_event(
    workflow_id: str,
    task_id: str,
    event_type: str,
    actor_type: str = "system",
    actor_id: str | None = None,
    data: dict | None = None,
) -> None:
    if not db_connection.async_session_factory:
        logger.warning("emit_event_skipped", reason="no_db", event_type=event_type)
        return

    try:
        async with db_connection.async_session_factory() as session:
            session.add(WorkflowEvent(
                workflow_id=workflow_id,
                task_id=task_id,
                event_type=event_type,
                actor_type=actor_type,
                actor_id=actor_id,
                data=data or {},
            ))
            await session.commit()
    except Exception as e:
        logger.warning(
            "emit_event_failed",
            event_type=event_type,
            task_id=task_id,
            error=str(e),
        )
