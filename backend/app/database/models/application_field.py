import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from app.database.types import GUID, JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class ApplicationField(BaseModel):
    __tablename__ = "application_fields"

    application_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("job_applications.id"), nullable=False
    )
    field_key: Mapped[str] = mapped_column(String(255), nullable=False)
    field_label: Mapped[str | None] = mapped_column(String(500), nullable=True)
    field_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    field_value: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_reference: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="MISSING")
    validation_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    application = relationship("JobApplication", back_populates="fields")
