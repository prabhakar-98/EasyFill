from app.tools.base import ToolContext, ToolOutput


async def get_user_profile(context: ToolContext, user_id: str) -> ToolOutput:
    """Get user profile data. Stub — will query user_profiles table."""
    return ToolOutput(success=False, error="Not implemented yet — Phase 8")


async def search_knowledge(context: ToolContext, query: str) -> ToolOutput:
    """Search RAG knowledge base. Stub — will use pgvector semantic search."""
    return ToolOutput(success=False, error="Not implemented yet — Phase 10")


async def get_job_posting(context: ToolContext, job_id: str) -> ToolOutput:
    """Get job posting details. Stub — will query job_postings table."""
    return ToolOutput(success=False, error="Not implemented yet — Phase 8")
