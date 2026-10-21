from abc import ABC, abstractmethod

from app.models.schemas import ModelRequest, ModelResponse


class ModelProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...
