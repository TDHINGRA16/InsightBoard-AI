"""
Transcript model for uploaded project transcripts.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import Profile
    from app.models.task import Task
    from app.models.job import Job
    from app.models.graph import Graph


class TranscriptStatus(str, enum.Enum):
    """Status of transcript analysis lifecycle."""

    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class Transcript(Base):
    """
    Transcript table for uploaded transcript text.

    Notes:
    - `content_hash` is unique (see migration) to deduplicate identical content across users.
    - The workspace is shared: any user can view any transcript/tasks.
      The `user_id` is retained to indicate who uploaded it.
    """

    __tablename__ = "transcripts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Uploader profile id",
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA256 of transcript text content",
    )
    status: Mapped[TranscriptStatus] = mapped_column(
        Enum(
            TranscriptStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            name="transcriptstatus",
        ),
        default=TranscriptStatus.UPLOADED,
        nullable=False,
        index=True,
    )
    analysis_result: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="transcripts",
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="transcript",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="transcript",
        cascade="all, delete-orphan",
    )
    graph: Mapped[Optional["Graph"]] = relationship(
        "Graph",
        back_populates="transcript",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_transcripts_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Transcript(id={self.id}, filename={self.filename}, status={self.status})>"

