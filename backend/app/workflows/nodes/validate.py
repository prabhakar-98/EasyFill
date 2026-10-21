import re

from app.logging import get_logger
from app.workflows.events import emit_event
from app.workflows.state import ResolvedField, WorkflowState

logger = get_logger("workflow.validate")

CONFIDENCE_THRESHOLD = 0.6

DATE_PATTERNS = [
    r"^\d{4}-\d{2}-\d{2}$",
    r"^\d{2}/\d{2}/\d{4}$",
    r"^\d{2}-\d{2}-\d{4}$",
    r"^\d{1,2}\s+\w+\s+\d{4}$",
    r"^\w+\s+\d{1,2},?\s+\d{4}$",
]

TIME_PATTERNS = [
    r"^\d{1,2}:\d{2}$",
    r"^\d{1,2}:\d{2}:\d{2}$",
    r"^\d{1,2}:\d{2}\s*[AaPp][Mm]$",
]


def _is_numeric(value: str) -> bool:
    try:
        float(value.replace(",", ""))
        return True
    except ValueError:
        return False


def _is_date(value: str) -> bool:
    return any(re.match(p, value.strip()) for p in DATE_PATTERNS)


def _is_time(value: str) -> bool:
    return any(re.match(p, value.strip()) for p in TIME_PATTERNS)


def _option_match(value: str, options: list[str]) -> bool:
    val_lower = value.lower().strip()
    return any(val_lower == opt.lower().strip() for opt in options)


def _validate_type_value(field: ResolvedField) -> str | None:
    """Returns a review_reason if the value doesn't match the field type, or None if valid."""
    value = field.get("value")
    if not value:
        return None

    field_type = field["type"]

    if field_type == "file_upload":
        return "file_upload"

    if field_type == "number":
        if not _is_numeric(value):
            return "value_type_mismatch: expected numeric value"

    if field_type == "date":
        if not _is_date(value):
            return "value_type_mismatch: expected date format"

    if field_type == "time":
        if not _is_time(value):
            return "value_type_mismatch: expected time format"

    if field_type in ("multiple_choice", "radio", "dropdown", "select", "linear_scale"):
        options = field.get("options") or []
        str_value = value if isinstance(value, str) else str(value)
        if options and not _option_match(str_value, options):
            return f"option_not_found: '{str_value}' not in {options}"

    if field_type == "checkbox":
        options = field.get("options") or []
        if options:
            items = value if isinstance(value, list) else [value]
            missing = [v for v in items if not _option_match(v, options)]
            if missing:
                return f"option_not_found: {missing} not in {options}"

    return None


async def validate_node(state: WorkflowState) -> dict:
    resolved_fields: list[ResolvedField] = state["resolved_fields"]

    confident: list[ResolvedField] = []
    uncertain: list[ResolvedField] = []

    for field in resolved_fields:
        reason = None

        if field["type"] == "file_upload":
            reason = "file_upload"
        elif field["value"] is None and field.get("required", False):
            reason = "no_value"
        elif field["confidence"] < CONFIDENCE_THRESHOLD:
            reason = "low_confidence"
        else:
            reason = _validate_type_value(field)

        if reason:
            updated = ResolvedField(
                **{**field, "needs_review": True, "review_reason": reason}
            )
            uncertain.append(updated)
        else:
            confident.append(field)

    logger.info(
        "fields_validated",
        total=len(resolved_fields),
        confident=len(confident),
        uncertain=len(uncertain),
        uncertain_details=[
            {
                "label": f["label"],
                "value": f["value"] if isinstance(f["value"], list) else (f["value"][:50] if f["value"] else None),
                "reason": f["review_reason"],
            }
            for f in uncertain
        ],
    )

    await emit_event(
        workflow_id=state.get("workflow_id", ""),
        task_id=state.get("task_id", ""),
        event_type="fields_validated",
        data={"confident": len(confident), "uncertain": len(uncertain)},
    )

    return {
        "confident_fields": confident,
        "uncertain_fields": uncertain,
        "status": "VALIDATING",
        "current_node": "validate",
        "events": [
            {
                "type": "fields_validated",
                "confident": len(confident),
                "uncertain": len(uncertain),
            }
        ],
    }
