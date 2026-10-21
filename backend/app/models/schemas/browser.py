from pydantic import BaseModel
from typing import Any


class BrowserOpenRequest(BaseModel):
    task_id: str
    url: str
    user_id: str | None = None


class BrowserError(BaseModel):
    code: str
    message: str


class BrowserResponse(BaseModel):
    success: bool
    task_id: str
    data: dict[str, Any] | None = None
    error: BrowserError | None = None
