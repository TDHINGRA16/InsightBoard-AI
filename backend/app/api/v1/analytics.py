"""
Analytics API endpoints - Dashboard metrics.
"""

from fastapi import APIRouter
from sqlalchemy import func

from app.dependencies import AuthUser, DbSession
from app.models.dependency import Dependency
from app.models.graph import Graph
from app.models.job import Job, JobStatus
from app.models.task import Task, TaskStatus
from app.models.transcript import Transcript, TranscriptStatus

router = APIRouter()


@router.get(
    "/dashboard",
    summary="Get dashboard analytics",
)
async def get_dashboard_analytics(
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get analytics summary for the dashboard.

    Returns counts and aggregations for transcripts, tasks,
    jobs, and project metrics.
    """
    user_id = current_user.id

    # Transcript stats
    transcript_count = (
        db.query(func.count(Transcript.id))
        .filter(Transcript.user_id == user_id)
        .scalar()
    )

    transcripts_by_status = (
        db.query(Transcript.status, func.count(Transcript.id))
        .filter(Transcript.user_id == user_id)
        .group_by(Transcript.status)
        .all()
    )

    # Task stats (via transcript ownership)
    task_count = (
        db.query(func.count(Task.id))
        .join(Transcript)
        .filter(Transcript.user_id == user_id)
        .scalar()
    )

    tasks_by_status = (
        db.query(Task.status, func.count(Task.id))
        .join(Transcript)
        .filter(Transcript.user_id == user_id)
        .group_by(Task.status)
        .all()
    )

    tasks_by_priority = (
        db.query(Task.priority, func.count(Task.id))
        .join(Transcript)
        .filter(Transcript.user_id == user_id)
        .group_by(Task.priority)
        .all()
    )

    # Dependency stats
    dependency_count = (
        db.query(func.count(Dependency.id))
        .join(Task, Dependency.task_id == Task.id)
        .join(Transcript)
        .filter(Transcript.user_id == user_id)
        .scalar()
    )

    avg_dependencies = dependency_count / task_count if task_count > 0 else 0

    # Job stats
    job_count = (
        db.query(func.count(Job.id))
        .filter(Job.user_id == user_id)
        .scalar()
    )

    jobs_by_status = (
        db.query(Job.status, func.count(Job.id))
        .filter(Job.user_id == user_id)
        .group_by(Job.status)
        .all()
    )

    # Graph metrics
    avg_critical_path_length = (
        db.query(func.avg(Graph.critical_path_length))
        .join(Transcript)
        .filter(
            Transcript.user_id == user_id,
            Graph.critical_path_length.isnot(None),
        )
        .scalar()
    ) or 0

    return {
        "success": True,
        "data": {
            "transcripts": {
                "total": transcript_count,
                "by_status": {
                    status.value: count
                    for status, count in transcripts_by_status
                },
            },
            "tasks": {
                "total": task_count,
                "by_status": {
                    status.value: count
                    for status, count in tasks_by_status
                },
                "by_priority": {
                    priority.value: count
                    for priority, count in tasks_by_priority
                },
            },
            "dependencies": {
                "total": dependency_count,
                "average_per_task": round(avg_dependencies, 2),
            },
            "jobs": {
                "total": job_count,
                "by_status": {
                    status.value: count
                    for status, count in jobs_by_status
                },
            },
            "metrics": {
                "average_critical_path_hours": round(float(avg_critical_path_length), 2),
            },
        },
    }


@router.get(
    "/summary",
    summary="Get quick summary",
)
async def get_quick_summary(
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get a quick summary of key metrics.
    """
    user_id = current_user.id

    # Quick counts
    transcript_count = (
        db.query(func.count(Transcript.id))
        .filter(Transcript.user_id == user_id)
        .scalar()
    )

    analyzed_count = (
        db.query(func.count(Transcript.id))
        .filter(
            Transcript.user_id == user_id,
            Transcript.status == TranscriptStatus.ANALYZED,
        )
        .scalar()
    )

    task_count = (
        db.query(func.count(Task.id))
        .join(Transcript)
        .filter(Transcript.user_id == user_id)
        .scalar()
    )

    completed_tasks = (
        db.query(func.count(Task.id))
        .join(Transcript)
        .filter(
            Transcript.user_id == user_id,
            Task.status == TaskStatus.COMPLETED,
        )
        .scalar()
    )

    pending_jobs = (
        db.query(func.count(Job.id))
        .filter(
            Job.user_id == user_id,
            Job.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING]),
        )
        .scalar()
    )

    return {
        "success": True,
        "data": {
            "transcripts": transcript_count,
            "analyzed_transcripts": analyzed_count,
            "tasks": task_count,
            "completed_tasks": completed_tasks,
            "completion_rate": round(
                completed_tasks / task_count * 100 if task_count > 0 else 0, 1
            ),
            "pending_jobs": pending_jobs,
        },
    }


@router.get(
    "/transcript/{transcript_id}",
    summary="Get transcript analytics",
)
async def get_transcript_analytics(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get analytics for a specific transcript.
    """
    from app.core.exceptions import NotFoundError

    # Verify ownership
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == transcript_id,
            Transcript.user_id == current_user.id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", transcript_id)

    # Task stats
    task_count = (
        db.query(func.count(Task.id))
        .filter(Task.transcript_id == transcript_id)
        .scalar()
    )

    tasks_by_status = (
        db.query(Task.status, func.count(Task.id))
        .filter(Task.transcript_id == transcript_id)
        .group_by(Task.status)
        .all()
    )

    tasks_by_priority = (
        db.query(Task.priority, func.count(Task.id))
        .filter(Task.transcript_id == transcript_id)
        .group_by(Task.priority)
        .all()
    )

    # Total estimated hours
    total_hours = (
        db.query(func.sum(Task.estimated_hours))
        .filter(Task.transcript_id == transcript_id)
        .scalar()
    ) or 0

    # Dependency stats
    dependency_count = (
        db.query(func.count(Dependency.id))
        .join(Task, Dependency.task_id == Task.id)
        .filter(Task.transcript_id == transcript_id)
        .scalar()
    )

    # Graph metrics
    graph = (
        db.query(Graph)
        .filter(Graph.transcript_id == transcript_id)
        .first()
    )

    critical_path_length = graph.critical_path_length if graph else None
    critical_path_tasks = len(graph.critical_path) if graph and graph.critical_path else 0

    return {
        "success": True,
        "data": {
            "transcript_id": transcript_id,
            "filename": transcript.filename,
            "status": transcript.status.value,
            "tasks": {
                "total": task_count,
                "by_status": {
                    status.value: count
                    for status, count in tasks_by_status
                },
                "by_priority": {
                    priority.value: count
                    for priority, count in tasks_by_priority
                },
            },
            "dependencies": {
                "total": dependency_count,
                "average_per_task": round(dependency_count / task_count, 2) if task_count > 0 else 0,
            },
            "estimates": {
                "total_hours": float(total_hours),
                "total_days": round(float(total_hours) / 8, 1),
            },
            "critical_path": {
                "length_hours": float(critical_path_length) if critical_path_length else None,
                "task_count": critical_path_tasks,
            },
        },
    }
