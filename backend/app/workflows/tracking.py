from contextlib import asynccontextmanager
from datetime import datetime

from app.database import connection as db_connection
from app.database.models.agent_run import AgentRun
from app.logging import get_logger
from app.models.gateway import gateway
from app.models.schemas import ModelRequest, ModelResponse

logger = get_logger("workflow.tracking")


async def tracked_generate(
    request: ModelRequest,
    task_id: str,
    workflow_id: str,
    agent_type: str,
) -> ModelResponse:
    started_at = datetime.utcnow()
    response: ModelResponse | None = None
    error_msg: str | None = None

    try:
        response = await gateway.generate(request)
        return response
    except Exception as e:
        error_msg = str(e)
        raise
    finally:
        if not db_connection.async_session_factory or not task_id or not workflow_id:
            return

        try:
            async with db_connection.async_session_factory() as session:
                run = AgentRun(
                    task_id=task_id,
                    workflow_id=workflow_id,
                    agent_type=agent_type,
                    model_provider=response.provider if response else None,
                    model_name=response.model if response else None,
                    status="COMPLETED" if response else "FAILED",
                    input_tokens=response.input_tokens if response else None,
                    output_tokens=response.output_tokens if response else None,
                    input_metadata={
                        "task_type": request.task_type,
                        "message_count": len(request.messages),
                    },
                    output_metadata={
                        "latency_ms": response.latency_ms,
                        "attempt": response.attempt,
                        "fallback_used": response.fallback_used,
                    } if response else None,
                    error_message=error_msg,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                )
                session.add(run)
                await session.commit()
        except Exception as e:
            logger.warning("agent_run_tracking_failed", error=str(e))
