from fastapi import APIRouter
from pydantic import BaseModel

from app.models.gateway import gateway
from app.models.schemas import ModelRequest, Message

router = APIRouter()


class LLMTestRequest(BaseModel):
    prompt: str
    task_type: str = "general"


@router.post("/test")
async def test_llm(req: LLMTestRequest):
    request = ModelRequest(
        messages=[Message(role="user", content=req.prompt)],
        task_type=req.task_type,
    )
    response = await gateway.generate(request)
    return {
        "content": response.content,
        "provider": response.provider,
        "model": response.model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "latency_ms": response.latency_ms,
        "fallback_used": response.fallback_used,
    }
