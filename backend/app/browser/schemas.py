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


class FormField(BaseModel):
    field_id: str
    label: str
    description: str | None = None
    placeholder: str | None = None
    validation: str | None = None
    type: str
    required: bool = False
    value: str | None = None
    options: list[str] | None = None
    section: int = 0


class FormData(BaseModel):
    form_title: str
    form_description: str | None = None
    total_fields: int
    required_fields: int
    fields: list[FormField]
