import time

import httpx

from app.config.settings import settings
from app.logging import get_logger
from app.models.provider import ModelProvider
from app.models.schemas import ModelRequest, ModelResponse

logger = get_logger("google_provider")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GoogleProvider(ModelProvider):
    name = "google"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.google_api_key
        self.model = model or settings.second_fallback_model

    async def generate(self, request: ModelRequest) -> ModelResponse:
        if not self.api_key:
            raise RuntimeError("Google API key not configured")

        contents = []
        system_instruction = None
        for m in request.messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        if request.response_format == "json":
            payload["generationConfig"]["responseMimeType"] = "application/json"

        url = f"{GEMINI_API_URL}/{self.model}:generateContent?key={self.api_key}"

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=settings.model_timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()

        latency_ms = int((time.monotonic() - start) * 1000)
        data = resp.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)

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
