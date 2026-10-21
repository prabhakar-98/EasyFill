import time

from anthropic import AsyncAnthropic

from app.config.settings import settings
from app.logging import get_logger
from app.models.provider import ModelProvider
from app.models.schemas import ModelRequest, ModelResponse

logger = get_logger("anthropic_provider")


class AnthropicProvider(ModelProvider):
    name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.fallback_model
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None

    async def generate(self, request: ModelRequest) -> ModelResponse:
        if not self.client:
            raise RuntimeError("Anthropic API key not configured")

        system_msg = ""
        messages = []
        for m in request.messages:
            if m.role == "system":
                system_msg = m.content
            else:
                messages.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if system_msg:
            kwargs["system"] = system_msg

        start = time.monotonic()
        response = await self.client.messages.create(**kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)

        content = response.content[0].text if response.content else ""
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

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
