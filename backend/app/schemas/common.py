"""
Common schemas used across the application.
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class BaseResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = True
    data: Any = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    success: bool = True
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class CurrentUser(BaseModel):
    """Authenticated user schema."""

    id: str = Field(..., description="User UUID from Supabase")
    email: str = Field(..., description="User email")
    full_name: str = Field(default="", description="User's full name")

    model_config = ConfigDict(from_attributes=True)


class DateRangeFilter(BaseModel):
    """Date range filter for queries."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ErrorDetail(BaseModel):
    """Error response detail."""

    detail: str
    code: str
    details: Optional[Any] = None
