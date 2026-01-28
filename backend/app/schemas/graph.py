"""
Graph schemas for visualization and critical path.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReactFlowNodeData(BaseModel):
    """Data payload for React Flow node."""

    label: str
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    assignee: Optional[str] = None
    duration: float = Field(default=0, description="Estimated hours")
    deadline: Optional[str] = None
    is_critical: bool = Field(default=False, description="Is on critical path")


class ReactFlowNodePosition(BaseModel):
    """Position for React Flow node."""

    x: float
    y: float


class ReactFlowNode(BaseModel):
    """React Flow node format."""

    id: str
    type: str = "taskNode"
    data: ReactFlowNodeData
    position: ReactFlowNodePosition


class ReactFlowEdge(BaseModel):
    """React Flow edge format."""

    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: bool = False
    type: str = "smoothstep"
    style: Optional[Dict[str, Any]] = None


class GraphData(BaseModel):
    """React Flow compatible graph data."""

    nodes: List[ReactFlowNode]
    edges: List[ReactFlowEdge]


class GraphMetrics(BaseModel):
    """Graph metrics summary."""

    nodes_count: int
    edges_count: int
    critical_path_length: Optional[float] = None
    total_duration_days: Optional[float] = None
    dependencies_avg: float = Field(
        default=0, description="Average dependencies per task"
    )


class GraphResponse(BaseModel):
    """Full graph response for visualization."""

    success: bool = True
    data: GraphData
    metrics: GraphMetrics
    transcript_id: str

    model_config = ConfigDict(from_attributes=True)


class SlackInfo(BaseModel):
    """Slack time for a task."""

    task_id: str
    task_title: str
    slack_hours: float
    earliest_start: float
    latest_start: float


class CriticalPathResponse(BaseModel):
    """Response for critical path analysis."""

    success: bool = True
    transcript_id: str
    critical_path: List[str] = Field(
        description="Ordered list of task IDs on critical path"
    )
    critical_path_titles: List[str] = Field(
        description="Ordered list of task titles on critical path"
    )
    total_duration_hours: float
    slack: List[SlackInfo] = Field(
        default=[], description="Slack time per non-critical task"
    )


class BottleneckInfo(BaseModel):
    """Bottleneck task information."""

    task_id: str
    task_title: str
    score: float = Field(description="Bottleneck score based on connectivity")
    out_degree: int = Field(description="Number of dependent tasks")
    in_degree: int = Field(description="Number of prerequisites")


class BottlenecksResponse(BaseModel):
    """Response for bottleneck analysis."""

    success: bool = True
    data: List[BottleneckInfo]
    message: str = "Bottleneck tasks identified"
