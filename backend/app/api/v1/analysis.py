"""
Analysis API endpoints - Start and manage analysis jobs.
"""

from fastapi import APIRouter

from app.core.exceptions import NotFoundError
from app.dependencies import AuthUser, DbSession
from app.models.job import Job, JobStatus, JobType
from app.models.transcript import Transcript
from app.schemas.job import AnalysisStartRequest, AnalysisStartResponse
from app.utils.idempotency import check_idempotency, generate_job_id
from app.workers.queue import enqueue_job
from app.workers.tasks import analyze_transcript_job

router = APIRouter()


@router.post(
    "/start",
    response_model=AnalysisStartResponse,
    summary="Start transcript analysis",
)
async def start_analysis(
    request: AnalysisStartRequest,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Start async analysis of a transcript.

    Uses LLM to extract tasks and dependencies.
    The analysis runs in the background - poll /jobs/{job_id} for status.

    Idempotency Logic:
    - If no existing job with same key: start new analysis
    - If existing job is QUEUED or PROCESSING: return existing job
    - If existing job is COMPLETED or FAILED and force=True: delete old tasks and re-analyze
    - If existing job is COMPLETED or FAILED and force=False: return existing job
    """
    from app.models.dependency import Dependency
    from app.models.task import Task

    # Verify transcript ownership
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == request.transcript_id,
            Transcript.user_id == current_user.id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", request.transcript_id)

    # Check idempotency
    exists, existing_job = check_idempotency(db, request.idempotency_key)

    if exists and existing_job:
        # Check if job is still running
        if existing_job.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
            # Return existing running job - true idempotency
            return AnalysisStartResponse(
                success=True,
                job_id=existing_job.id,
                is_existing=True,
                message="Analysis job already in progress",
                data={
                    "status": existing_job.status.value,
                    "progress": existing_job.progress,
                },
            )

        # Job is completed or failed
        if not request.force:
            # Return existing completed job without re-processing
            return AnalysisStartResponse(
                success=True,
                job_id=existing_job.id,
                is_existing=True,
                message="Analysis already completed. Use force=true to re-analyze.",
                data={
                    "status": existing_job.status.value,
                    "progress": existing_job.progress,
                    "can_reanalyze": True,
                },
            )

        # Force re-analysis: Delete old tasks and dependencies for this transcript
        # Dependencies are cascade deleted with tasks, but be explicit
        db.query(Dependency).filter(
            Dependency.task_id.in_(
                db.query(Task.id).filter(Task.transcript_id == request.transcript_id)
            )
        ).delete(synchronize_session=False)

        db.query(Task).filter(Task.transcript_id == request.transcript_id).delete(
            synchronize_session=False
        )

        # Delete the old job to allow new idempotency key
        db.delete(existing_job)
        db.commit()

    # Generate job ID
    job_id = generate_job_id("analyze", request.transcript_id)

    # Create job record
    job = Job(
        id=job_id,
        user_id=current_user.id,
        transcript_id=request.transcript_id,
        job_type=JobType.ANALYZE,
        status=JobStatus.QUEUED,
        idempotency_key=request.idempotency_key,
        progress=0,
    )

    db.add(job)
    db.commit()

    # Enqueue background job
    enqueue_job(
        analyze_transcript_job,
        request.transcript_id,
        current_user.id,
        job_id,
        job_id=job_id,
        job_timeout=600,
    )

    return AnalysisStartResponse(
        success=True,
        job_id=job_id,
        is_existing=False,
        message="Analysis job started" if not request.force else "Re-analysis job started",
        data={
            "status": "queued",
            "progress": 0,
        },
    )


@router.post(
    "/retry/{transcript_id}",
    response_model=AnalysisStartResponse,
    summary="Retry failed analysis",
)
async def retry_analysis(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Retry analysis for a failed transcript.

    Creates a new job with a new idempotency key.
    """
    import uuid

    # Verify transcript ownership
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

    # Generate new job ID and idempotency key
    job_id = generate_job_id("analyze", transcript_id)
    idempotency_key = f"retry-{transcript_id}-{uuid.uuid4().hex[:8]}"

    # Create job record
    job = Job(
        id=job_id,
        user_id=current_user.id,
        transcript_id=transcript_id,
        job_type=JobType.ANALYZE,
        status=JobStatus.QUEUED,
        idempotency_key=idempotency_key,
        progress=0,
    )

    db.add(job)
    db.commit()

    # Enqueue background job
    enqueue_job(
        analyze_transcript_job,
        transcript_id,
        current_user.id,
        job_id,
        job_id=job_id,
        job_timeout=600,
    )

    return AnalysisStartResponse(
        success=True,
        job_id=job_id,
        is_existing=False,
        message="Analysis retry job started",
        data={
            "status": "queued",
            "progress": 0,
        },
    )
