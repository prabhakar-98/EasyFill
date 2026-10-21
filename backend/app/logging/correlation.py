import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        task_id = request.headers.get("X-Task-ID", "")
        user_id = request.headers.get("X-User-ID", "")

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            task_id=task_id,
            user_id=user_id,
        )

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        return response
