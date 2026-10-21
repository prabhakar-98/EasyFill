from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CanonicalEmbedding(Base):
    __tablename__ = "canonical_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    label_text: Mapped[str] = mapped_column(String(500), nullable=False)
    embedding = mapped_column(Vector(768), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default="seed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
