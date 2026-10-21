import time

from openai import AsyncOpenAI

from app.config.settings import settings
from app.logging import get_logger
from app.models.provider import ModelProvider
from app.models.schemas import ModelRequest, ModelResponse

logger = get_logger("openai_provider")


class OpenAIProvider(ModelProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.model_name
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def generate(self, request: ModelRequest) -> ModelResponse:
        if not self.client:
            raise RuntimeError("OpenAI API key not configured")

        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        start = time.monotonic()
        response = await self.client.chat.completions.create(**kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)

        content = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

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
