"""
Graphs API endpoints - Graph visualization and critical path.
"""

from fastapi import APIRouter

from app.core.exceptions import NotFoundError
from app.dependencies import AuthUser, DbSession
from app.models.transcript import Transcript
from app.schemas.graph import (
    BottlenecksResponse,
    CriticalPathResponse,
    GraphResponse,
)
from app.services.cache_service import cache_service
from app.services.dependency_service import DependencyService
from app.services.graph_service import GraphService

router = APIRouter()


@router.get(
    "/{transcript_id}",
    response_model=GraphResponse,
    summary="Get graph data",
)
async def get_graph(
    transcript_id: str,
    use_cache: bool = True,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get React Flow compatible graph data for visualization.

    Returns nodes and edges formatted for React Flow.
    """
    # Shared workspace: any user can view graphs
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == transcript_id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", transcript_id)

    # Check cache
    if use_cache:
        cached = cache_service.get_cached_graph(transcript_id)
        if cached:
            return GraphResponse(
                success=True,
                transcript_id=transcript_id,
                data=cached["data"],
                metrics=cached["metrics"],
            )

    # Generate graph data
    graph_service = GraphService(db)
    dependency_service = DependencyService(db)

    # Get critical path for highlighting
    nx_graph = dependency_service.build_dependency_graph(transcript_id)
    critical_path = []

    try:
        is_valid, _ = dependency_service.validate_dag(transcript_id)
        if is_valid and nx_graph.nodes():
            critical_path, _, _ = dependency_service.compute_critical_path(nx_graph)
    except Exception:
        pass

    graph_data, metrics = graph_service.generate_react_flow_data(
        transcript_id,
        critical_path=critical_path,
    )

    # Cache result
    cache_service.cache_graph(
        transcript_id,
        {"data": graph_data.model_dump(), "metrics": metrics.model_dump()},
    )

    return GraphResponse(
        success=True,
        transcript_id=transcript_id,
        data=graph_data,
        metrics=metrics,
    )


@router.get(
    "/{transcript_id}/critical-path",
    response_model=CriticalPathResponse,
    summary="Get critical path",
)
async def get_critical_path(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Compute and return the critical path for a transcript.

    The critical path is the longest sequence of dependent tasks
    that determines the minimum project duration.
    """
    # Shared workspace: any user can view critical path
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == transcript_id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", transcript_id)

    dependency_service = DependencyService(db)

    # Validate DAG first
    is_valid, cycle = dependency_service.validate_dag(transcript_id)

    if not is_valid:
        return CriticalPathResponse(
            success=False,
            transcript_id=transcript_id,
            critical_path=[],
            critical_path_titles=[],
            total_duration_hours=0,
            slack=[],
        )

    # Build graph and compute critical path
    nx_graph = dependency_service.build_dependency_graph(transcript_id)

    if not nx_graph.nodes():
        return CriticalPathResponse(
            success=True,
            transcript_id=transcript_id,
            critical_path=[],
            critical_path_titles=[],
            total_duration_hours=0,
            slack=[],
        )

    critical_path, total_duration, slack = dependency_service.compute_critical_path(
        nx_graph
    )

    # Get titles for critical path tasks
    critical_path_titles = [
        nx_graph.nodes[node].get("title", "Unknown")
        for node in critical_path
    ]

    # Format slack info
    slack_info = []
    for task_id, slack_hours in slack.items():
        if slack_hours > 0:
            slack_info.append({
                "task_id": task_id,
                "task_title": nx_graph.nodes[task_id].get("title", "Unknown"),
                "slack_hours": slack_hours,
                "earliest_start": 0,  # Would need full CPM data
                "latest_start": slack_hours,
            })

    return CriticalPathResponse(
        success=True,
        transcript_id=transcript_id,
        critical_path=critical_path,
        critical_path_titles=critical_path_titles,
        total_duration_hours=total_duration,
        slack=slack_info,
    )


@router.get(
    "/{transcript_id}/bottlenecks",
    response_model=BottlenecksResponse,
    summary="Get bottleneck tasks",
)
async def get_bottlenecks(
    transcript_id: str,
    top_n: int = 5,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Identify bottleneck tasks based on connectivity.

    Bottlenecks are tasks with many dependents that could
    block significant portions of the project if delayed.
    """
    # Shared workspace: any user can view bottlenecks
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == transcript_id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", transcript_id)

    dependency_service = DependencyService(db)

    # Build graph
    nx_graph = dependency_service.build_dependency_graph(transcript_id)

    if not nx_graph.nodes():
        return BottlenecksResponse(
            success=True,
            data=[],
            message="No tasks found",
        )

    # Detect bottlenecks
    bottlenecks = dependency_service.detect_bottlenecks(nx_graph, top_n=top_n)

    return BottlenecksResponse(
        success=True,
        data=bottlenecks,
        message=f"Found {len(bottlenecks)} potential bottlenecks",
    )


@router.post(
    "/{transcript_id}/refresh",
    response_model=GraphResponse,
    summary="Refresh graph data",
)
async def refresh_graph(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Force refresh of graph data, ignoring cache.

    Use after modifying tasks or dependencies.
    """
    # Invalidate cache
    cache_service.invalidate_analysis(transcript_id)

    # Get fresh data
    return await get_graph(
        transcript_id=transcript_id,
        use_cache=False,
        db=db,
        current_user=current_user,
    )
