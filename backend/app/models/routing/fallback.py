from app.config.settings import settings
from app.logging import get_logger
from app.models.provider import ModelProvider
from app.models.schemas import ModelRequest, ModelResponse

logger = get_logger("fallback")


class FallbackChain:
    def __init__(self, providers: list[ModelProvider], max_retries: int = 3):
        self.providers = providers
        self.max_retries = max_retries

    async def execute(self, request: ModelRequest) -> ModelResponse:
        last_error: Exception | None = None

        for provider_index, provider in enumerate(self.providers):
            is_fallback = provider_index > 0

            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(
                        "model_attempt",
                        provider=provider.name,
                        attempt=attempt,
                        fallback=is_fallback,
                        task_type=request.task_type,
                    )

                    response = await provider.generate(request)
                    response.attempt = attempt
                    response.fallback_used = is_fallback

                    return response

                except Exception as e:
                    last_error = e
                    logger.warning(
                        "model_attempt_failed",
                        provider=provider.name,
                        attempt=attempt,
                        fallback=is_fallback,
                        error=str(e),
                    )

            logger.error(
                "provider_exhausted",
                provider=provider.name,
                max_retries=self.max_retries,
            )

        logger.critical("all_providers_failed", task_type=request.task_type)
        raise RuntimeError(f"All model providers failed: {last_error}")
