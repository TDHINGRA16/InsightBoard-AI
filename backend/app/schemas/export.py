"""
Export schemas for data export operations.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Supported export formats."""

    JSON = "json"
    CSV = "csv"
    GANTT = "gantt"


class ExportRequest(BaseModel):
    """Request for exporting transcript data."""

    transcript_id: str = Field(..., description="UUID of transcript to export")
    format: ExportFormat = Field(default=ExportFormat.JSON)
    include_dependencies: bool = Field(
        default=True, description="Include dependency data"
    )
    include_graph: bool = Field(
        default=False, description="Include graph layout data"
    )


class ExportResponse(BaseModel):
    """Response containing exported data."""

    success: bool = True
    format: ExportFormat
    data: Any = Field(description="Exported data in requested format")
    filename: str = Field(description="Suggested filename for download")
    content_type: str = Field(description="MIME type for the export")


class GanttTask(BaseModel):
    """Task in Gantt chart format."""

    id: str
    name: str
    start: str = Field(description="ISO date string")
    end: str = Field(description="ISO date string")
    progress: float = Field(default=0, ge=0, le=100)
    dependencies: str = Field(default="", description="Comma-separated task IDs")
    assignee: Optional[str] = None
    type: str = Field(default="task")


class GanttExportData(BaseModel):
    """Gantt chart export data."""

    project_name: str
    start_date: str
    tasks: list[GanttTask]
