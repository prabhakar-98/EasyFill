from typing import Literal

from pydantic import BaseModel, field_validator

SUPPORTED_FIELD_TYPES = {
    "text", "short_text", "long_text",
    "radio", "multiple_choice", "checkbox",
    "number", "time", "date",
    "select", "dropdown",
}

FieldType = Literal[
    "text", "short_text", "long_text",
    "radio", "multiple_choice", "checkbox",
    "number", "time", "date",
    "select", "dropdown",
    "unknown",
]


class FieldInfo(BaseModel):
    index: int
    label: str
    type: FieldType = "text"
    required: bool = False
    description: str | None = None
    options: list[str] = []
    validation: dict | None = None

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        if v not in SUPPORTED_FIELD_TYPES:
            return "unknown"
        return v


class AutofillRequest(BaseModel):
    url: str | None = None
    form_title: str | None = None
    form_description: str | None = None
    fields: list[FieldInfo]


class AutofillResponse(BaseModel):
    values: dict[str, str | list[str]]
    matched: int
    total: int


class WorkflowResponse(BaseModel):
    values: dict[str, str | list[str]]
    matched: int
    total: int
    task_id: str | None = None
    needs_review: list[dict] | None = None


class ApprovalResponse(BaseModel):
    id: str
    label: str
    value: str | None
    confidence: float
    reason: str | None
    status: str


class ApprovalActionRequest(BaseModel):
    action: Literal["approve", "modify", "reject"]
    value: str | None = None
    comment: str | None = None


class SubmitCaptureRequest(BaseModel):
    task_id: str
    final_values: dict[str, str | list[str]]
