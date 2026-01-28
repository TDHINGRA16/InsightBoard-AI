"""
Webhook model for event subscriptions.
"""

import enum
import secrets
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import Profile


class WebhookEventType(str, enum.Enum):
    """Types of events that can trigger webhooks."""

    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    EXPORT_COMPLETED = "export.completed"


class Webhook(Base):
    """
    Webhook table for event subscriptions.

    Users can subscribe to events and receive HTTP callbacks.
    """

    __tablename__ = "webhooks"

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
    event_type: Mapped[WebhookEventType] = mapped_column(
        Enum(WebhookEventType),
        nullable=False,
    )
    endpoint_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    secret_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=lambda: secrets.token_hex(32),
        comment="HMAC signing key",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    failed_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="webhooks",
    )

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, event={self.event_type}, active={self.is_active})>"
