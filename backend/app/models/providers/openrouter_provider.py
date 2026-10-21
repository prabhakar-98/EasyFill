import time

import httpx

from app.config.settings import settings
from app.logging import get_logger
from app.models.provider import ModelProvider
from app.models.schemas import ModelRequest, ModelResponse

logger = get_logger("openrouter_provider")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider(ModelProvider):
    name = "openrouter"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.openrouter_model

    async def generate(self, request: ModelRequest) -> ModelResponse:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=settings.model_timeout) as client:
            resp = await client.post(OPENROUTER_API_URL, json=payload, headers=headers)
            resp.raise_for_status()

        latency_ms = int((time.monotonic() - start) * 1000)
        data = resp.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        logger.info(
            "model_response",
            provider=self.name,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )

        return ModelResponse(
            content=content,
            provider=self.name,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )

    async def is_available(self) -> bool:
        return bool(self.api_key)
