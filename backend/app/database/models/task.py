import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from app.database.types import GUID, JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class Task(BaseModel):
    __tablename__ = "tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    input: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user = relationship("User", back_populates="tasks")
    workflows = relationship("Workflow", back_populates="task")
    job_applications = relationship("JobApplication", back_populates="task")
