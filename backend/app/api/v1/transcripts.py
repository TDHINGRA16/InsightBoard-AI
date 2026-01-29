"""
Transcripts API endpoints.
"""

import math
from typing import Optional

import uuid

from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile

from app.dependencies import AuthUser, DbSession
from app.models.transcript import TranscriptStatus
from app.schemas.common import BaseResponse
from app.schemas.transcript import (
    TranscriptListResponse,
    TranscriptResponse,
    TranscriptUploadResponse,
)
from app.services.transcript_service import TranscriptService

router = APIRouter()


@router.post(
    "/upload",
    response_model=TranscriptUploadResponse,
    summary="Upload a transcript file",
)
async def upload_transcript(
    file: UploadFile = File(..., description="Transcript file (.txt or .pdf)"),
    idempotency_key: Optional[str] = Form(default=None),
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Upload a project transcript for analysis.

    Accepts .txt and .pdf files up to 50MB.
    Use idempotency_key to prevent duplicate uploads.
    """
    service = TranscriptService(db)

    # Read file content
    content = await file.read()

    # Upload and save
    transcript, is_duplicate = service.upload_transcript(
        user_id=current_user.id,
        filename=file.filename,
        file_content=content,
        idempotency_key=idempotency_key,
    )

    return TranscriptUploadResponse(
        success=True,
        data=TranscriptResponse(
            id=str(transcript.id),
            user_id=str(transcript.user_id),
            filename=transcript.filename,
            file_type=transcript.file_type,
            size_bytes=transcript.size_bytes,
            status=transcript.status,
            content_hash=transcript.content_hash,
            analysis_result=transcript.analysis_result,
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
        ),
        message=(
            "Duplicate transcript detected. You can view existing analysis or start a re-analysis."
            if is_duplicate
            else "Transcript uploaded successfully"
        ),
        is_duplicate=is_duplicate,
    )


@router.get(
    "",
    response_model=TranscriptListResponse,
    summary="List transcripts",
)
async def list_transcripts(
    status: Optional[TranscriptStatus] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    List ALL transcripts (shared workspace).

    Supports filtering by status and filename search.
    """
    service = TranscriptService(db)

    transcripts, total = service.list_transcripts(
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return TranscriptListResponse(
        success=True,
        data=[
            {
                "id": str(t.id),
                "filename": t.filename,
                "file_type": t.file_type,
                "size_bytes": t.size_bytes,
                "status": t.status,
                "created_at": t.created_at,
                "task_count": len(t.tasks) if t.tasks else 0,
            }
            for t in transcripts
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{transcript_id}",
    response_model=BaseResponse,
    summary="Get transcript details",
)
async def get_transcript(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get details of a specific transcript.
    """
    service = TranscriptService(db)

    transcript = service.get_transcript(transcript_id)

    return BaseResponse(
        success=True,
        data=TranscriptResponse(
            id=str(transcript.id),
            user_id=str(transcript.user_id),
            filename=transcript.filename,
            file_type=transcript.file_type,
            size_bytes=transcript.size_bytes,
            status=transcript.status,
            content_hash=transcript.content_hash,
            analysis_result=transcript.analysis_result,
            error_message=transcript.error_message,
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
            task_count=len(transcript.tasks) if transcript.tasks else 0,
        ),
    )


@router.delete(
    "/{transcript_id}",
    response_model=BaseResponse,
    summary="Delete a transcript",
)
async def delete_transcript(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Delete a transcript and all associated tasks/dependencies.
    """
    # Keep delete restricted to uploader to avoid cross-user destructive actions.
    from app.models.transcript import Transcript
    transcript = (
        db.query(Transcript)
        .filter(Transcript.id == transcript_id, Transcript.user_id == current_user.id)
        .first()
    )
    if not transcript:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Transcript", transcript_id)

    service = TranscriptService(db)
    service.delete_transcript(transcript_id)

    return BaseResponse(
        success=True,
        message="Transcript deleted successfully",
    )


@router.get(
    "/{transcript_id}/content",
    response_model=BaseResponse,
    summary="Get transcript content",
)
async def get_transcript_content(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get the text content of a transcript.
    """
    service = TranscriptService(db)

    transcript = service.get_transcript(transcript_id)

    return BaseResponse(
        success=True,
        data={
            "id": str(transcript.id),
            "filename": transcript.filename,
            "content": transcript.content,
        },
    )


@router.put(
    "/{transcript_id}",
    response_model=BaseResponse,
    summary="Update transcript content (pre-analysis)",
)
async def update_transcript(
    transcript_id: str,
    body: dict = Body(...),
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Update transcript content before analysis starts.

    Shared workspace note: any user can edit ONLY if analysis hasn't started yet.
    Once analyzing/analyzed/failed, edits are blocked to avoid inconsistent tasks/graphs.
    """
    from app.models.transcript import Transcript, TranscriptStatus
    import hashlib

    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Transcript", transcript_id)

    if transcript.status != TranscriptStatus.UPLOADED:
        # Analysis has started or completed/failed.
        return BaseResponse(
            success=False,
            message="Cannot edit transcript - analysis already started",
        )

    new_content = (body or {}).get("content")
    if not isinstance(new_content, str) or not new_content.strip():
        return BaseResponse(success=False, message="Content is required")

    new_hash = hashlib.sha256(new_content.encode()).hexdigest()

    # If the edited content matches an existing transcript, treat it as a duplicate edit attempt.
    existing = (
        db.query(Transcript)
        .filter(Transcript.content_hash == new_hash, Transcript.id != transcript.id)
        .first()
    )
    if existing:
        return BaseResponse(
            success=True,
            data={
                "status": "duplicate_found",
                "existing_transcript_id": str(existing.id),
            },
            message="This edited transcript matches existing content. Use the existing transcript or re-analyze it.",
        )

    transcript.content = new_content
    transcript.content_hash = new_hash
    db.commit()
    db.refresh(transcript)

    return BaseResponse(
        success=True,
        data={"status": "updated", "transcript_id": str(transcript.id)},
        message="Transcript updated successfully",
    )


@router.post(
    "/{transcript_id}/re-analyze",
    response_model=BaseResponse,
    summary="Re-analyze a transcript (force)",
)
async def reanalyze_transcript(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Start a new analysis run for an existing transcript.

    This uses the existing transcript content (no duplicate transcript rows),
    and force-replaces the extracted tasks/dependencies for this transcript.
    """
    from app.models.dependency import Dependency
    from app.models.job import Job, JobStatus, JobType
    from app.models.task import Task
    from app.models.transcript import Transcript, TranscriptStatus
    from app.utils.idempotency import generate_job_id
    from app.workers.queue import enqueue_job
    from app.workers.tasks import analyze_transcript_job

    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Transcript", transcript_id)

    # Delete old tasks and dependencies (force semantics)
    db.query(Dependency).filter(
        Dependency.task_id.in_(db.query(Task.id).filter(Task.transcript_id == transcript_id))
    ).delete(synchronize_session=False)
    db.query(Task).filter(Task.transcript_id == transcript_id).delete(synchronize_session=False)

    # New job idempotency key (always unique for re-analysis)
    idempotency_key = f"reanalyze-{transcript_id}-{uuid.uuid4().hex[:10]}"
    job_id = generate_job_id("analyze", transcript_id)

    job = Job(
        id=job_id,
        user_id=current_user.id,
        transcript_id=transcript.id,
        job_type=JobType.ANALYZE,
        status=JobStatus.QUEUED,
        idempotency_key=idempotency_key,
        progress=0,
    )
    db.add(job)

    transcript.status = TranscriptStatus.ANALYZING
    db.commit()

    enqueue_job(
        analyze_transcript_job,
        transcript_id,
        current_user.id,
        job_id,
        job_id=job_id,
        job_timeout=600,
    )

    return BaseResponse(
        success=True,
        data={"status": "analysis_queued", "job_id": job_id, "transcript_id": transcript_id},
        message="Re-analysis job started",
    )
