"""
Task model for project tasks extracted from transcripts.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.transcript import Transcript
    from app.models.dependency import Dependency


class TaskPriority(str, enum.Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, enum.Enum):
    """Task completion status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Task(Base):
    """
    Task table for project tasks extracted from transcripts.

    Tasks can have dependencies on other tasks and are
    used to build the dependency graph.
    """

    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    transcript_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    assignee: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    estimated_hours: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=0,
    )
    actual_hours: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        default=0,
    )
    position_x: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=0,
        comment="X position for graph visualization",
    )
    position_y: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        default=0,
        comment="Y position for graph visualization",
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
    transcript: Mapped["Transcript"] = relationship(
        "Transcript",
        back_populates="tasks",
    )

    # Dependencies where this task is the dependent
    dependencies: Mapped[List["Dependency"]] = relationship(
        "Dependency",
        foreign_keys="Dependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    # Dependencies where this task is depended upon
    dependents: Mapped[List["Dependency"]] = relationship(
        "Dependency",
        foreign_keys="Dependency.depends_on_task_id",
        back_populates="depends_on_task",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_tasks_transcript_status", "transcript_id", "status"),
        Index("ix_tasks_transcript_priority", "transcript_id", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title[:30]}..., status={self.status})>"
