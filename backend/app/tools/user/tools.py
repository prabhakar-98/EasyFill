from app.tools.base import ToolContext, ToolOutput


async def request_input(context: ToolContext, field_id: str, question: str) -> ToolOutput:
    """Ask user for missing information. Stub — will pause workflow and notify frontend."""
    return ToolOutput(success=False, error="Not implemented yet — Phase 9")


async def record_response(context: ToolContext, field_id: str, response: str) -> ToolOutput:
    """Store user's response. Stub — will save to personalized_memories."""
    return ToolOutput(success=False, error="Not implemented yet — Phase 9")
