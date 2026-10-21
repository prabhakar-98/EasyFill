from typing import Any, Callable, Awaitable

from app.logging import get_logger
from app.tools.base import ToolContext, ToolOutput

logger = get_logger("tool_registry")

ToolFunction = Callable[..., Awaitable[ToolOutput]]


class ToolInfo:
    def __init__(self, name: str, fn: ToolFunction, category: str, description: str):
        self.name = name
        self.fn = fn
        self.category = category
        self.description = description


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolInfo] = {}
        self._allowlist: set[str] | None = None

    def register(self, name: str, fn: ToolFunction, category: str, description: str) -> None:
        self._tools[name] = ToolInfo(name=name, fn=fn, category=category, description=description)
        logger.debug("tool_registered", name=name, category=category)

    def set_allowlist(self, allowed: set[str]) -> None:
        self._allowlist = allowed

    def is_allowed(self, name: str) -> bool:
        if self._allowlist is None:
            return name in self._tools
        return name in self._allowlist

    async def execute(self, name: str, context: ToolContext, **kwargs: Any) -> ToolOutput:
        if name not in self._tools:
            logger.error("tool_not_found", name=name)
            return ToolOutput(success=False, error=f"Tool '{name}' not found")

        if not self.is_allowed(name):
            logger.warning("tool_not_allowed", name=name, task_id=context.task_id)
            return ToolOutput(success=False, error=f"Tool '{name}' is not allowed")

        tool = self._tools[name]

        logger.info("tool_executing", name=name, category=tool.category, task_id=context.task_id)

        try:
            result = await tool.fn(context=context, **kwargs)
            logger.info(
                "tool_executed",
                name=name,
                task_id=context.task_id,
                success=result.success,
            )
            return result
        except Exception as e:
            logger.error("tool_execution_failed", name=name, task_id=context.task_id, error=str(e))
            return ToolOutput(success=False, error=str(e))

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": t.name, "category": t.category, "description": t.description}
            for t in self._tools.values()
        ]

    def list_by_category(self, category: str) -> list[dict[str, str]]:
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
            if t.category == category
        ]


registry = ToolRegistry()
