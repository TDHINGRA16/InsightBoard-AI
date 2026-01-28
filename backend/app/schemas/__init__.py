"""Schemas module - Pydantic v2 models for API."""

from app.schemas.common import (
    BaseResponse,
    CurrentUser,
    PaginatedResponse,
    PaginationParams,
)
from app.schemas.transcript import (
    TranscriptCreate,
    TranscriptResponse,
    TranscriptListResponse,
)
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
)
from app.schemas.dependency import (
    DependencyCreate,
    DependencyResponse,
)
from app.schemas.job import (
    AnalysisStartRequest,
    AnalysisStartResponse,
    JobResponse,
    JobListResponse,
)
from app.schemas.graph import (
    GraphResponse,
    CriticalPathResponse,
    ReactFlowNode,
    ReactFlowEdge,
)
from app.schemas.webhook import (
    WebhookCreate,
    WebhookResponse,
    WebhookListResponse,
)
from app.schemas.export import (
    ExportRequest,
    ExportResponse,
)

__all__ = [
    # Common
    "BaseResponse",
    "CurrentUser",
    "PaginatedResponse",
    "PaginationParams",
    # Transcript
    "TranscriptCreate",
    "TranscriptResponse",
    "TranscriptListResponse",
    # Task
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    # Dependency
    "DependencyCreate",
    "DependencyResponse",
    # Job
    "AnalysisStartRequest",
    "AnalysisStartResponse",
    "JobResponse",
    "JobListResponse",
    # Graph
    "GraphResponse",
    "CriticalPathResponse",
    "ReactFlowNode",
    "ReactFlowEdge",
    # Webhook
    "WebhookCreate",
    "WebhookResponse",
    "WebhookListResponse",
    # Export
    "ExportRequest",
    "ExportResponse",
]
