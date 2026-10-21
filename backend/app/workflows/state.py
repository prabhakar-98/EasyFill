from __future__ import annotations

from operator import add
from typing import Annotated, Literal, TypedDict

FieldType = Literal[
    "text", "short_text", "long_text",
    "radio", "multiple_choice", "checkbox",
    "number", "time", "date",
    "select", "dropdown",
    "linear_scale", "grid",
    "file_upload", "unknown", "other",
]

MappingSource = Literal["alias", "fixed", "vector", "llm", "unmapped"]

ValueSource = Literal["profile", "memory", "rag", "llm", "none"]

WorkflowStatus = Literal[
    "PENDING",
    "RUNNING",
    "MAPPING_FIELDS",
    "RESOLVING_VALUES",
    "VALIDATING",
    "WAITING_FOR_HUMAN",
    "STORING_RESULT",
    "COMPLETED",
    "FAILED",
]


class FieldInput(TypedDict):
    index: int
    label: str
    type: FieldType
    required: bool
    description: str | None
    options: list[str] | None
    validation: dict | None


class MappedField(TypedDict):
    index: int
    label: str
    type: FieldType
    required: bool
    description: str | None
    options: list[str]
    canonical_key: str | None
    mapping_confidence: float
    mapping_source: MappingSource
    field_embedding: list[float] | None
    validation: dict | None


class ResolvedField(TypedDict):
    index: int
    label: str
    type: FieldType
    required: bool
    options: list[str]
    canonical_key: str | None
    value: str | list[str] | None
    value_source: ValueSource
    confidence: float
    needs_review: bool
    review_reason: str | None
    field_embedding: list[float] | None


class WorkflowState(TypedDict):
    user_id: str
    task_id: str
    workflow_id: str
    url: str
    form_title: str
    form_description: str
    fields: list[FieldInput]

    status: WorkflowStatus

    mapped_fields: list[MappedField]
    resolved_fields: list[ResolvedField]
    confident_fields: list[ResolvedField]
    uncertain_fields: list[ResolvedField]
    final_fields: list[ResolvedField]

    values: dict[str, str | list[str]]
    matched: int
    total: int

    events: Annotated[list[dict], add]
    errors: Annotated[list[dict], add]
    current_node: str
