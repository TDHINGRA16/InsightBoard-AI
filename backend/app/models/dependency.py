"""
Dependency model for task dependencies.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.task import Task


class DependencyType(str, enum.Enum):
    """Types of task dependencies."""

    BLOCKS = "blocks"  # Task A must finish before Task B starts
    PRECEDES = "precedes"  # Task A should ideally finish before Task B
    PARENT_OF = "parent_of"  # Task A is a parent/container of Task B
    RELATED_TO = "related_to"  # Tasks are related but not blocking


class Dependency(Base):
    """
    Dependency table for task dependencies.

    Represents edges in the task dependency graph.
    """

    __tablename__ = "dependencies"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    task_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The task that depends on another",
    )
    depends_on_task_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The task being depended upon",
    )
    dependency_type: Mapped[DependencyType] = mapped_column(
        # Persist enum *values* (e.g. "blocks") rather than names ("BLOCKS")
        # to match existing Postgres enum values.
        Enum(
            DependencyType,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=DependencyType.BLOCKS,
        nullable=False,
    )
    lag_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Days between completion and start",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        foreign_keys=[task_id],
        back_populates="dependencies",
    )
    depends_on_task: Mapped["Task"] = relationship(
        "Task",
        foreign_keys=[depends_on_task_id],
        back_populates="dependents",
    )

    __table_args__ = (
        CheckConstraint(
            "task_id != depends_on_task_id",
            name="check_no_self_dependency",
        ),
        Index(
            "ix_dependencies_unique_pair",
            "task_id",
            "depends_on_task_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<Dependency(task={self.task_id} depends_on={self.depends_on_task_id}, type={self.dependency_type})>"
