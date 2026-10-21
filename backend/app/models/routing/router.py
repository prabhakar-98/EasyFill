from dataclasses import dataclass

from app.config.settings import settings


@dataclass
class RouteConfig:
    provider: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.0
    timeout: int = 30


TASK_ROUTES: dict[str, RouteConfig] = {
    "field_mapping": RouteConfig(
        provider=settings.model_provider,
        model=settings.ollama_model if settings.model_provider == "ollama" else settings.model_name,
        max_tokens=100,
        temperature=0.0,
        timeout=10,
    ),
    "answer_drafting": RouteConfig(
        provider=settings.model_provider,
        model=settings.ollama_model if settings.model_provider == "ollama" else settings.model_name,
        max_tokens=2000,
        temperature=0.3,
        timeout=30,
    ),
    "browser_tool_call": RouteConfig(
        provider=settings.model_provider,
        model=settings.ollama_model if settings.model_provider == "ollama" else settings.model_name,
        max_tokens=500,
        temperature=0.0,
        timeout=15,
    ),
    "general": RouteConfig(
        provider=settings.model_provider,
        model=settings.ollama_model if settings.model_provider == "ollama" else settings.model_name,
        max_tokens=1000,
        temperature=0.0,
        timeout=30,
    ),
}

NO_LLM_TASKS = frozenset({"simple_lookup", "submission"})


def get_route(task_type: str) -> RouteConfig:
    return TASK_ROUTES.get(task_type, TASK_ROUTES["general"])


def requires_llm(task_type: str) -> bool:
    return task_type not in NO_LLM_TASKS
