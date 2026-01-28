"""
User profile model - maps to Supabase auth.users.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.transcript import Transcript
    from app.models.job import Job
    from app.models.webhook import Webhook
    from app.models.audit_log import AuditLog


class Profile(Base):
    """
    User profile table.

    Maps to Supabase auth.users via the same UUID.
    Stores additional user metadata not in Supabase.
    """

    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        comment="Same as Supabase auth.users.id",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        default="",
    )
    avatar_url: Mapped[str] = mapped_column(
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
    transcripts: Mapped[List["Transcript"]] = relationship(
        "Transcript",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    webhooks: Mapped[List["Webhook"]] = relationship(
        "Webhook",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
    )

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, email={self.email})>"
