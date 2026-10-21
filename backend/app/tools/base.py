from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import Page
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ToolContext:
    task_id: str
    page: Page
    db: AsyncSession | None = None
    user_id: str | None = None


@dataclass
class ToolOutput:
    success: bool
    data: Any = None
    error: str | None = None
