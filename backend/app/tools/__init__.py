from app.tools.base import ToolContext, ToolOutput
from app.tools.registry import registry

from app.tools.retrieval.tools import get_user_profile, search_knowledge, get_job_posting
from app.tools.validation.tools import validate_field, validate_form
from app.tools.user.tools import request_input, record_response


def register_all_tools() -> None:
    # Retrieval tools (stubs)
    registry.register("get_user_profile", get_user_profile, "retrieval", "Get user profile data")
    registry.register("search_knowledge", search_knowledge, "retrieval", "Search RAG knowledge base")
    registry.register("get_job_posting", get_job_posting, "retrieval", "Get job posting details")

    # Validation tools (stubs)
    registry.register("validate_field", validate_field, "validation", "Validate a field value")
    registry.register("validate_form", validate_form, "validation", "Validate entire form")

    # User tools (stubs)
    registry.register("request_input", request_input, "user", "Ask user for missing info")
    registry.register("record_response", record_response, "user", "Store user response")


__all__ = [
    "ToolContext",
    "ToolOutput",
    "registry",
    "register_all_tools",
]
