import uuid

from sqlalchemy import BigInteger, ForeignKey, String, Text
from app.database.types import GUID, JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel, SoftDeleteMixin


class Document(SoftDeleteMixin, BaseModel):
    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONType, nullable=True)

    user = relationship("User", back_populates="documents")
