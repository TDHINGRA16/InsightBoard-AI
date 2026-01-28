"""
Graph model for storing computed dependency graphs.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.transcript import Transcript


class Graph(Base):
    """
    Graph table for storing computed dependency graph data.

    Caches React Flow-compatible graph data and critical path metrics.
    """

    __tablename__ = "graphs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    transcript_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    nodes_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    edges_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    critical_path: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Ordered list of task IDs in critical path",
    )
    critical_path_length: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Total duration of critical path in hours",
    )
    total_duration_days: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    slack_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Slack time per task {task_id: hours}",
    )
    graph_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="React Flow compatible nodes/edges",
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
        back_populates="graphs",
    )

    def __repr__(self) -> str:
        return f"<Graph(id={self.id}, nodes={self.nodes_count}, edges={self.edges_count})>"
