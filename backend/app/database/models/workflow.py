import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class Workflow(BaseModel):
    __tablename__ = "workflows"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tasks.id"), nullable=False
    )
    workflow_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="RUNNING")
    current_node: Mapped[str | None] = mapped_column(String(150), nullable=True)
    graph_thread_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    paused_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    task = relationship("Task", back_populates="workflows")
    checkpoints = relationship("WorkflowCheckpoint", back_populates="workflow")
    approvals = relationship("Approval", back_populates="workflow")
    events = relationship("WorkflowEvent", back_populates="workflow")
    agent_runs = relationship("AgentRun", back_populates="workflow")
