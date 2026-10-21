from sqlalchemy import String, Text
from app.database.types import JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class JobPosting(BaseModel):
    __tablename__ = "job_postings"

    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    applications = relationship("JobApplication", back_populates="job_posting")
