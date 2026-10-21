import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from app.database.types import GUID, JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class Approval(BaseModel):
    __tablename__ = "approvals"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tasks.id"), nullable=False
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workflows.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    payload: Mapped[dict] = mapped_column(JSONType, nullable=False)
    user_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)

    workflow = relationship("Workflow", back_populates="approvals")
