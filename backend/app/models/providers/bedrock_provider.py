import asyncio
import json
import time

import boto3

from app.config.settings import settings
from app.logging import get_logger
from app.models.provider import ModelProvider
from app.models.schemas import ModelRequest, ModelResponse

logger = get_logger("bedrock_provider")


class BedrockProvider(ModelProvider):
    name = "bedrock"

    def __init__(self, model: str | None = None):
        self.model = model or settings.bedrock_model

        session_kwargs = {}
        if settings.bedrock_profile:
            session_kwargs["profile_name"] = settings.bedrock_profile
        if settings.bedrock_access_key_id and settings.bedrock_secret_access_key:
            session_kwargs["aws_access_key_id"] = settings.bedrock_access_key_id
            session_kwargs["aws_secret_access_key"] = settings.bedrock_secret_access_key
            if settings.bedrock_session_token:
                session_kwargs["session_token"] = settings.bedrock_session_token

        session = boto3.Session(**session_kwargs)
        self._client = session.client(
            "bedrock-runtime",
            region_name=settings.bedrock_region,
        )

    async def generate(self, request: ModelRequest) -> ModelResponse:
        system_parts = []
        messages = []

        for m in request.messages:
            if m.role == "system":
                system_parts.append({"text": m.content})
            else:
                messages.append({
                    "role": m.role,
                    "content": [{"text": m.content}],
                })

        kwargs = {
            "modelId": self.model,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": request.max_tokens,
                "temperature": request.temperature,
            },
        }

        if system_parts:
            kwargs["system"] = system_parts

        start = time.monotonic()
        response = await asyncio.to_thread(self._client.converse, **kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)

        output = response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])
        content = content_blocks[0]["text"] if content_blocks else ""

        usage = response.get("usage", {})
        input_tokens = usage.get("inputTokens", 0)
        output_tokens = usage.get("outputTokens", 0)

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
        has_explicit_keys = bool(
            settings.bedrock_access_key_id and settings.bedrock_secret_access_key
        )
        has_profile = bool(settings.bedrock_profile)

        if has_explicit_keys or has_profile:
            return True

        # Fall back to default credential chain (IAM role, env vars, ~/.aws/credentials)
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            return credentials is not None
        except Exception:
            return False
