from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel, SoftDeleteMixin


class User(SoftDeleteMixin, BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    auth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    auth_provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    preferences = relationship("UserPreference", back_populates="user")
    documents = relationship("Document", back_populates="user")
    tasks = relationship("Task", back_populates="user")
