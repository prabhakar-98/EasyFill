import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from app.database.types import GUID, JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class UserPreference(BaseModel):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "key"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(150), nullable=False)
    value: Mapped[dict] = mapped_column(JSONType, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="preferences")
