"""
Dependency schemas for task relationships.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.dependency import DependencyType


class DependencyBase(BaseModel):
    """Base dependency fields."""

    task_id: str = Field(..., description="UUID of dependent task")
    depends_on_task_id: str = Field(..., description="UUID of prerequisite task")
    dependency_type: DependencyType = DependencyType.BLOCKS
    lag_days: int = Field(default=0, ge=0, description="Days between completion and start")


class DependencyCreate(DependencyBase):
    """Request schema for creating a dependency."""

    pass


class DependencyResponse(DependencyBase):
    """Single dependency response."""

    id: str
    created_at: datetime
    task_title: Optional[str] = Field(default=None, description="Title of dependent task")
    depends_on_title: Optional[str] = Field(
        default=None, description="Title of prerequisite task"
    )

    model_config = ConfigDict(from_attributes=True)


class DependencyListResponse(BaseModel):
    """List of dependencies response."""

    success: bool = True
    data: List[DependencyResponse]
    total: int


class TaskDependenciesResponse(BaseModel):
    """Response showing a task's dependencies and dependents."""

    success: bool = True
    task_id: str
    task_title: str
    dependencies: List[DependencyResponse] = Field(
        default=[], description="Tasks this task depends on"
    )
    dependents: List[DependencyResponse] = Field(
        default=[], description="Tasks that depend on this task"
    )


class DependencyValidationResponse(BaseModel):
    """Response for dependency validation check."""

    success: bool = True
    is_valid: bool
    message: str
    cycle_detected: Optional[List[str]] = Field(
        default=None, description="Task IDs in the detected cycle, if any"
    )
