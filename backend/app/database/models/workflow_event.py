import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from app.database.types import GUID, JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workflows.id"), nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tasks.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    data: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    workflow = relationship("Workflow", back_populates="events")
