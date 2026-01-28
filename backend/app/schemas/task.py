"""
Task schemas for CRUD operations.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """Base task fields."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assignee: Optional[str] = None
    estimated_hours: Optional[float] = Field(default=0, ge=0)


class TaskCreate(TaskBase):
    """Request schema for creating a task."""

    transcript_id: str = Field(..., description="UUID of parent transcript")


class TaskUpdate(BaseModel):
    """Request schema for updating a task."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assignee: Optional[str] = None
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    actual_hours: Optional[float] = Field(default=None, ge=0)


class TaskResponse(TaskBase):
    """Single task response."""

    id: str
    transcript_id: str
    actual_hours: Optional[float] = 0
    position_x: float = 0
    position_y: float = 0
    created_at: datetime
    updated_at: datetime
    dependencies_count: int = Field(
        default=0,
        description="Number of tasks this task depends on",
    )
    dependents_count: int = Field(
        default=0,
        description="Number of tasks depending on this task",
    )

    model_config = ConfigDict(from_attributes=True)


class TaskWithDependencies(TaskResponse):
    """Task with full dependency information."""

    dependencies: List[str] = Field(
        default=[],
        description="IDs of tasks this task depends on",
    )
    dependents: List[str] = Field(
        default=[],
        description="IDs of tasks that depend on this task",
    )


class TaskListResponse(BaseModel):
    """Paginated task list response."""

    success: bool = True
    data: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskSingleResponse(BaseModel):
    """Single task API response wrapper."""

    success: bool = True
    data: TaskWithDependencies


class TaskBulkCreateRequest(BaseModel):
    """Request for bulk task creation."""

    tasks: List[TaskCreate]


class TaskBulkResponse(BaseModel):
    """Response for bulk task operations."""

    success: bool = True
    data: List[TaskResponse]
    created_count: int
    message: str
