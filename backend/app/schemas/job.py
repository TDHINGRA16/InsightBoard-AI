"""
Job schemas for background processing.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus, JobType


class AnalysisStartRequest(BaseModel):
    """Request to start transcript analysis."""

    transcript_id: str = Field(..., description="UUID of transcript to analyze")
    idempotency_key: str = Field(
        ..., description="Unique key for idempotent analysis requests"
    )


class AnalysisStartResponse(BaseModel):
    """Response after starting analysis."""

    success: bool = True
    data: dict = Field(default_factory=dict)
    message: str = "Analysis job started"
    job_id: str
    is_existing: bool = Field(
        default=False,
        description="True if returning existing job (idempotent)",
    )


class JobBase(BaseModel):
    """Base job fields."""

    job_type: JobType
    status: JobStatus
    progress: int = Field(ge=0, le=100)


class JobResponse(JobBase):
    """Single job response."""

    id: str
    user_id: str
    transcript_id: str
    result: Optional[dict] = None
    error_message: Optional[str] = None
    idempotency_key: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListItem(BaseModel):
    """Job item for list responses."""

    id: str
    job_type: JobType
    status: JobStatus
    progress: int
    transcript_id: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """Paginated job list response."""

    success: bool = True
    data: List[JobListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobStatusResponse(BaseModel):
    """Response for job status check."""

    success: bool = True
    data: JobResponse


class JobProgressUpdate(BaseModel):
    """Internal schema for updating job progress."""

    progress: int = Field(ge=0, le=100)
    status: Optional[JobStatus] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None
