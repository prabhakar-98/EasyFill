import sys
import logging
import logging.handlers
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from app.config.settings import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

SKIP_KEYS = frozenset({
    "logger_name", "timestamp", "level", "event", "app", "env",
    "component", "logger", "trace_id",
})


def _add_app_info(logger: Any, method_name: str, event_dict: dict) -> dict:
    return event_dict


def _drop_empty_values(logger: Any, method_name: str, event_dict: dict) -> dict:
    return {k: v for k, v in event_dict.items() if v != "" and v is not None}


def _uvicorn_style_renderer(logger: Any, method_name: str, event_dict: dict) -> str:
    level = event_dict.get("level", "info").upper()
    event = event_dict.get("event", "")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    extras = {k: v for k, v in event_dict.items() if k not in SKIP_KEYS and v != "" and v is not None}
    extra_str = " | ".join(f"{k}={v}" for k, v in extras.items())

    if extra_str:
        return f"{level}:     {ts} | {event} | {extra_str}"
    return f"{level}:     {ts} | {event}"


def setup_logging() -> None:
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_app_info,
        _drop_empty_values,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    json_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=shared_processors,
    )

    # Terminal handler — uvicorn-style readable output
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _uvicorn_style_renderer,
        ],
        foreign_pre_chain=shared_processors,
    )
    console_handler.setFormatter(console_formatter)

    # File handler — all logs, JSON, daily rotation, 30 days
    file_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "easyfill.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(json_formatter)

    # Error file handler — ERROR+ only
    error_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "error.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)

    # Audit file handler — audit events only
    audit_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / "audit.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    audit_handler.setFormatter(json_formatter)
    audit_handler.addFilter(logging.Filter("easyfill.audit"))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    audit_logger = logging.getLogger("easyfill.audit")
    audit_logger.addHandler(audit_handler)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class Logger:
    def __init__(self, component: str) -> None:
        self._logger = structlog.get_logger(component=component)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._logger.debug(event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info(event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning(event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error(event, **kwargs)

    def critical(self, event: str, **kwargs: Any) -> None:
        self._logger.critical(event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        self._logger.exception(event, **kwargs)


def get_logger(component: str) -> Logger:
    return Logger(component=component)
