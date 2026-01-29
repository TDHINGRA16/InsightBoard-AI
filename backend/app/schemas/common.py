"""
Shared schemas used across the API.
"""

from typing import Any, Optional

from pydantic import BaseModel


class BaseResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None


class CurrentUser(BaseModel):
    """
    Minimal authenticated user payload extracted from Supabase JWT.
    """

    id: str
    email: Optional[str] = None
    role: str = "authenticated"


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel):
    success: bool = True
    data: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

