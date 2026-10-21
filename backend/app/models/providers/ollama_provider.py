import time

import httpx

from app.config.settings import settings
from app.logging import get_logger
from app.models.provider import ModelProvider
from app.models.schemas import ModelRequest, ModelResponse

logger = get_logger("ollama_provider")


class OllamaProvider(ModelProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model

    async def generate(self, request: ModelRequest) -> ModelResponse:
        prompt = "\n".join(m.content for m in request.messages)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if request.response_format == "json":
            payload["format"] = "json"

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=settings.model_timeout) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()

        latency_ms = int((time.monotonic() - start) * 1000)
        data = resp.json()

        content = data.get("response", "")
        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

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
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
