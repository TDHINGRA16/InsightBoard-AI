"""
Job model for background processing jobs.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import Profile
    from app.models.transcript import Transcript


class JobType(str, enum.Enum):
    """Types of background jobs."""

    ANALYZE = "analyze"
    EXPORT = "export"
    OPTIMIZE = "optimize"


class JobStatus(str, enum.Enum):
    """Status of background jobs."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """
    Job table for tracking background processing jobs.

    Stores RQ job metadata and results for async operations.
    """

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        comment="RQ job ID",
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transcript_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type: Mapped[JobType] = mapped_column(
        Enum(
            JobType,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="jobtype",
        ),
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="jobstatus",
        ),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True,
    )
    result: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Job result data (counts, summary, etc.)",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Progress percentage 0-100",
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="jobs",
    )
    transcript: Mapped["Transcript"] = relationship(
        "Transcript",
        back_populates="jobs",
    )

    __table_args__ = (
        Index("ix_jobs_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"
