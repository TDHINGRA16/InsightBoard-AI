"""
Audit log model for tracking resource changes.
"""

import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import BigInteger, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import Profile


class AuditAction(str, enum.Enum):
    """Types of audited actions."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class ResourceType(str, enum.Enum):
    """Types of auditable resources."""

    TRANSCRIPT = "transcript"
    TASK = "task"
    DEPENDENCY = "dependency"
    WEBHOOK = "webhook"
    JOB = "job"


class AuditLog(Base):
    """
    Audit log table for tracking resource changes.

    Stores before/after values for compliance and debugging.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction),
        nullable=False,
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType),
        nullable=False,
    )
    resource_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    old_values: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    new_values: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        back_populates="audit_logs",
    )

    __table_args__ = (
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_user_date", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type}:{self.resource_id})>"
