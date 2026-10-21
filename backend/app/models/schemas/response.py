from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResponse:
    content: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    attempt: int = 1
    fallback_used: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
