import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class JobApplication(BaseModel):
    __tablename__ = "job_applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tasks.id"), nullable=False
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("job_postings.id"), nullable=True
    )
    application_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DISCOVERED")
    auth_required: Mapped[bool] = mapped_column(Boolean, default=False)
    authenticated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    submission_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    task = relationship("Task", back_populates="job_applications")
    job_posting = relationship("JobPosting", back_populates="applications")
    fields = relationship("ApplicationField", back_populates="application")
