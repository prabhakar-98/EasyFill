from app.tools.base import ToolContext, ToolOutput


async def validate_field(context: ToolContext, field_id: str, value: str, field_type: str) -> ToolOutput:
    """Validate a single field value. Stub — will check format, required, constraints."""
    return ToolOutput(success=False, error="Not implemented yet — Phase 8")


async def validate_form(context: ToolContext) -> ToolOutput:
    """Validate all fields before submission. Stub — will check entire form."""
    return ToolOutput(success=False, error="Not implemented yet — Phase 8")
