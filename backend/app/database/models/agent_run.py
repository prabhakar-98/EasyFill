import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from app.database.types import GUID, JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class AgentRun(BaseModel):
    __tablename__ = "agent_runs"

    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tasks.id"), nullable=False
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workflows.id"), nullable=False
    )
    agent_type: Mapped[str] = mapped_column(String(80), nullable=False)
    model_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="RUNNING")
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_metadata: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    output_metadata: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    workflow = relationship("Workflow", back_populates="agent_runs")
    tool_executions = relationship("ToolExecution", back_populates="agent_run")
