import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from app.database.types import GUID, JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class ToolExecution(BaseModel):
    __tablename__ = "tool_executions"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agent_runs.id"), nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(150), nullable=False)
    tool_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="RUNNING")
    input_metadata: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    output_metadata: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    policy_decision: Mapped[str | None] = mapped_column(String(30), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    agent_run = relationship("AgentRun", back_populates="tool_executions")
