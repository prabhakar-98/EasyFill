from app.config.settings import settings
from app.logging import get_logger
from app.models.provider import ModelProvider
from app.models.routing import get_route, requires_llm, FallbackChain
from app.models.schemas import ModelRequest, ModelResponse
from app.models.providers.ollama_provider import OllamaProvider
from app.models.providers.openrouter_provider import OpenRouterProvider
from app.models.providers.openai_provider import OpenAIProvider
from app.models.providers.anthropic_provider import AnthropicProvider
from app.models.providers.google_provider import GoogleProvider
from app.models.providers.bedrock_provider import BedrockProvider

logger = get_logger("gateway")

PROVIDER_MAP = {
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "bedrock": BedrockProvider,
}


class ModelGateway:
    def __init__(self):
        self._providers: dict[str, ModelProvider] = {}
        self._fallback_chain: FallbackChain | None = None

    async def initialize(self) -> None:
        primary_name = settings.model_provider
        primary_cls = PROVIDER_MAP.get(primary_name)

        if not primary_cls:
            raise ValueError(f"Unknown model provider: {primary_name}")

        primary = primary_cls()
        self._providers[primary_name] = primary

        chain = [primary]

        fallback_configs = [
            (settings.fallback_provider, settings.fallback_model),
            (settings.second_fallback_provider, settings.second_fallback_model),
        ]

        for fb_name, fb_model in fallback_configs:
            if fb_name and fb_name != primary_name:
                fb_cls = PROVIDER_MAP.get(fb_name)
                if fb_cls:
                    fb = fb_cls(model=fb_model)
                    if await fb.is_available():
                        self._providers[fb_name] = fb
                        chain.append(fb)
                        logger.info("fallback_registered", provider=fb_name, model=fb_model)

        self._fallback_chain = FallbackChain(
            providers=chain,
            max_retries=settings.model_max_retries,
        )

        available = [p.name for p in chain]
        logger.info(
            "gateway_initialized",
            primary=primary_name,
            providers=available,
        )

    async def generate(self, request: ModelRequest) -> ModelResponse:
        if not requires_llm(request.task_type):
            raise ValueError(f"Task '{request.task_type}' should not use LLM")

        if not self._fallback_chain:
            raise RuntimeError("Gateway not initialized. Call initialize() first.")

        route = get_route(request.task_type)
        request.temperature = request.temperature or route.temperature
        request.max_tokens = request.max_tokens or route.max_tokens

        logger.info(
            "gateway_request",
            task_type=request.task_type,
            route_provider=route.provider,
            route_model=route.model,
        )

        response = await self._fallback_chain.execute(request)

        logger.info(
            "gateway_response",
            task_type=request.task_type,
            provider=response.provider,
            model=response.model,
        )

        return response

    def get_provider(self, name: str) -> ModelProvider | None:
        return self._providers.get(name)


gateway = ModelGateway()
