import asyncio
import time
from abc import ABC, abstractmethod

import httpx
from sqlalchemy import text

from app.config.settings import settings
from app.database import connection as db_connection
from app.logging import get_logger

logger = get_logger("embedding")


class EmbeddingBackend(ABC):
    @abstractmethod
    async def embed(self, input_text: str) -> list[float]: ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class OllamaBackend(EmbeddingBackend):

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def embed(self, input_text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=settings.model_timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model, "input": input_text},
            )
            resp.raise_for_status()
        return resp.json()["embeddings"][0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            async with httpx.AsyncClient(timeout=settings.model_timeout * len(texts)) as client:
                resp = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": texts},
                )
                resp.raise_for_status()
            return resp.json()["embeddings"]
        except (httpx.HTTPStatusError, KeyError):
            pass
        return [await self.embed(t) for t in texts]


class OnnxBackend(EmbeddingBackend):

    def __init__(self, model_name: str):
        from pathlib import Path
        from fastembed import TextEmbedding

        cache_dir = Path.home() / ".cache" / "fastembed"
        model_slug = model_name.replace("/", "--")
        cached = any(cache_dir.glob(f"*{model_slug}*")) if cache_dir.exists() else False

        if cached:
            logger.info("onnx_model_loading_from_cache", model=model_name)
        else:
            logger.info("onnx_model_downloading", model=model_name)

        self._model = TextEmbedding(model_name)
        logger.info("onnx_model_ready", model=model_name)

    async def embed(self, input_text: str) -> list[float]:
        embeddings = await asyncio.to_thread(
            lambda: list(self._model.embed([input_text]))
        )
        return embeddings[0].tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = await asyncio.to_thread(
            lambda: list(self._model.embed(texts))
        )
        return [e.tolist() for e in embeddings]


class EmbeddingService:

    def __init__(self, backend: EmbeddingBackend):
        self._backend = backend

    async def embed(self, input_text: str) -> list[float]:
        start = time.monotonic()
        embedding = await self._backend.embed(input_text)
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.debug(
            "text_embedded",
            backend=type(self._backend).__name__,
            dimensions=len(embedding),
            latency_ms=latency_ms,
        )
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        start = time.monotonic()
        embeddings = await self._backend.embed_batch(texts)
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "batch_embedded",
            backend=type(self._backend).__name__,
            count=len(texts),
            latency_ms=latency_ms,
        )
        return embeddings

    async def search_canonical(
        self,
        query_embedding: list[float],
        threshold: float = 0.75,
        limit: int = 5,
    ) -> list[dict]:
        if not db_connection.async_session_factory:
            logger.error("search_canonical_failed", reason="database not initialized")
            return []

        async with db_connection.async_session_factory() as session:
            emb_str = str(query_embedding)
            result = await session.execute(
                text("""
                    SELECT canonical_key, label_text,
                           1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                    FROM canonical_embeddings
                    WHERE embedding IS NOT NULL
                      AND 1 - (embedding <=> CAST(:embedding AS vector)) >= :threshold
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :limit
                """),
                {
                    "embedding": emb_str,
                    "threshold": threshold,
                    "limit": limit,
                },
            )

            matches = [
                {
                    "canonical_key": row.canonical_key,
                    "label_text": row.label_text,
                    "similarity": round(float(row.similarity), 4),
                }
                for row in result
            ]

        logger.debug(
            "canonical_search",
            matches=len(matches),
            threshold=threshold,
        )
        return matches

    async def search_user_data(
        self,
        user_id: str,
        query_embedding: list[float],
        threshold: float = 0.70,
        limit: int = 5,
    ) -> list[dict]:
        if not db_connection.async_session_factory:
            return []

        try:
            async with db_connection.async_session_factory() as session:
                emb_str = str(query_embedding)
                result = await session.execute(
                    text("""
                        SELECT source_type, field_key, text_content,
                               1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                        FROM user_data_embeddings
                        WHERE user_id = CAST(:user_id AS uuid)
                          AND embedding IS NOT NULL
                        ORDER BY embedding <=> CAST(:embedding AS vector)
                        LIMIT :limit
                    """),
                    {
                        "embedding": emb_str,
                        "user_id": user_id,
                        "threshold": threshold,
                        "limit": limit,
                    },
                )

                matches = [
                    {
                        "source_type": row.source_type,
                        "field_key": row.field_key,
                        "text_content": row.text_content,
                        "similarity": round(float(row.similarity), 4),
                    }
                    for row in result
                ]

            logger.debug(
                "user_data_search",
                user_id=user_id,
                matches=len(matches),
                threshold=threshold,
            )
            return matches
        except Exception as e:
            logger.warning("user_data_search_unavailable", error=str(e))
            return []


def _create_backend() -> EmbeddingBackend:
    if settings.embedding_backend == "onnx":
        return OnnxBackend(settings.onnx_embedding_model)
    return OllamaBackend(settings.ollama_base_url, settings.embedding_model)


embedding_service = EmbeddingService(_create_backend())
