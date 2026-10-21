import logging
from typing import Any

import structlog

_audit_logger = structlog.wrap_logger(
    logging.getLogger("easyfill.audit"),
    wrapper_class=structlog.stdlib.BoundLogger,
)


def audit_event(
    event: str,
    *,
    task_id: str = "",
    user_id: str = "",
    component: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    _audit_logger.info(
        event,
        task_id=task_id,
        user_id=user_id,
        component=component,
        audit=True,
        metadata=metadata or {},
    )
