"""
Transcript schemas for upload and response.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.transcript import TranscriptStatus


class TranscriptBase(BaseModel):
    """Base transcript fields."""

    filename: str
    file_type: str
    size_bytes: int


class TranscriptCreate(BaseModel):
    """Request schema for transcript upload metadata."""

    idempotency_key: Optional[str] = Field(
        default=None,
        description="Unique key for idempotent uploads",
    )


class TranscriptResponse(TranscriptBase):
    """Single transcript response."""

    id: str
    user_id: str
    status: TranscriptStatus
    content_hash: str
    analysis_result: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    task_count: Optional[int] = Field(
        default=None,
        description="Number of tasks extracted (if analyzed)",
    )

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime) -> str:
        """Ensure datetime is timezone-aware and serialize as ISO format."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


class TranscriptListItem(BaseModel):
    """Transcript item for list responses."""

    id: str
    filename: str
    file_type: str
    size_bytes: int
    status: TranscriptStatus
    created_at: datetime
    task_count: int = 0

    @field_serializer("created_at")
    def serialize_datetime(self, dt: datetime) -> str:
        """Ensure datetime is timezone-aware and serialize as ISO format."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


class TranscriptListResponse(BaseModel):
    """Paginated transcript list response."""

    success: bool = True
    data: List[TranscriptListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class TranscriptUploadResponse(BaseModel):
    """Response after successful transcript upload."""

    success: bool = True
    data: TranscriptResponse
    message: str = "Transcript uploaded successfully"
    is_duplicate: bool = Field(
        default=False,
        description="True if this was a duplicate upload (idempotent)",
    )
