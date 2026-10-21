from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ModelRequest:
    messages: list[Message]
    task_type: str = "general"
    temperature: float = 0.0
    max_tokens: int = 1000
    response_format: str = "text"
    metadata: dict[str, Any] = field(default_factory=dict)
