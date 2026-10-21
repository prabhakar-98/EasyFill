from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.browser.session_manager import session_manager
from app.browser.schemas import BrowserResponse, BrowserError
from app.tools import registry
from app.tools.base import ToolContext
from app.logging import get_logger

router = APIRouter()
logger = get_logger("routes_tools")


class ToolExecuteRequest(BaseModel):
    task_id: str
    tool_name: str
    params: dict[str, Any] = {}


@router.post("/execute", response_model=BrowserResponse)
async def execute_tool(request: ToolExecuteRequest):
    session = session_manager.get_session(request.task_id)
    if not session:
        return BrowserResponse(
            success=False,
            task_id=request.task_id,
            error=BrowserError(code="SESSION_NOT_FOUND", message=f"No session for task {request.task_id}"),
        )

    context = ToolContext(
        task_id=request.task_id,
        page=session.page,
    )

    result = await registry.execute(request.tool_name, context, **request.params)

    if not result.success:
        return BrowserResponse(
            success=False,
            task_id=request.task_id,
            error=BrowserError(code="TOOL_FAILED", message=result.error or "Unknown error"),
        )

    return BrowserResponse(
        success=True,
        task_id=request.task_id,
        data=result.data,
    )


@router.get("/list")
async def list_tools():
    return {
        "total": len(registry.list_tools()),
        "tools": registry.list_tools(),
    }


@router.get("/list/{category}")
async def list_tools_by_category(category: str):
    tools = registry.list_by_category(category)
    return {
        "category": category,
        "total": len(tools),
        "tools": tools,
    }
