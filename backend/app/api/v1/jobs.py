"""
Jobs API endpoints - Query job status and history.
"""

import math
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import desc

from app.core.exceptions import NotFoundError
from app.dependencies import AuthUser, DbSession
from app.models.job import Job, JobStatus, JobType
from app.schemas.job import JobListResponse, JobResponse, JobStatusResponse

router = APIRouter()


@router.get(
    "",
    response_model=JobListResponse,
    summary="List jobs",
)
async def list_jobs(
    status: Optional[JobStatus] = Query(default=None),
    job_type: Optional[JobType] = Query(default=None),
    transcript_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    List jobs for the current user.

    Filter by status, job_type, or transcript_id.
    """
    query = db.query(Job).filter(Job.user_id == current_user.id)

    if status:
        query = query.filter(Job.status == status)
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if transcript_id:
        query = query.filter(Job.transcript_id == transcript_id)

    # Count
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    jobs = (
        query.order_by(desc(Job.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return JobListResponse(
        success=True,
        data=[
            {
                "id": j.id,
                "job_type": j.job_type,
                "status": j.status,
                "progress": j.progress,
                "transcript_id": str(j.transcript_id),
                "created_at": j.created_at,
                "completed_at": j.completed_at,
            }
            for j in jobs
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
)
async def get_job_status(
    job_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get the current status of a job.

    Poll this endpoint to track job progress.
    """
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.user_id == current_user.id,
        )
        .first()
    )

    if not job:
        raise NotFoundError("Job", job_id)

    return JobStatusResponse(
        success=True,
        data=JobResponse(
            id=job.id,
            user_id=str(job.user_id),
            transcript_id=str(job.transcript_id),
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            result=job.result,
            error_message=job.error_message,
            idempotency_key=job.idempotency_key,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
        ),
    )


@router.delete(
    "/{job_id}",
    summary="Cancel a job",
)
async def cancel_job(
    job_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Cancel a queued or processing job.

    Note: Jobs already in progress may not be immediately cancelled.
    """
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.user_id == current_user.id,
        )
        .first()
    )

    if not job:
        raise NotFoundError("Job", job_id)

    # Only allow cancelling queued or processing jobs
    if job.status not in [JobStatus.QUEUED, JobStatus.PROCESSING]:
        return {
            "success": False,
            "message": f"Cannot cancel job with status: {job.status.value}",
        }

    # Update status
    job.status = JobStatus.FAILED
    job.error_message = "Cancelled by user"
    db.commit()

    return {
        "success": True,
        "message": "Job cancelled",
    }
