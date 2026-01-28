"""
Transcript model for uploaded project transcripts.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import Profile
    from app.models.task import Task
    from app.models.job import Job
    from app.models.graph import Graph


class TranscriptStatus(str, enum.Enum):
    """Status of transcript processing."""

    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class Transcript(Base):
    """
    Transcript table for storing uploaded project transcripts.

    Contains the raw content and metadata about processing status.
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
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="File extension (.txt, .pdf)",
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Extracted text content",
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA-256 hash for deduplication",
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
        comment="Cached analysis summary",
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
    graphs: Mapped[List["Graph"]] = relationship(
        "Graph",
        back_populates="transcript",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_transcripts_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Transcript(id={self.id}, filename={self.filename}, status={self.status})>"
