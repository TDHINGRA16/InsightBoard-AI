"""
Transcripts API endpoints.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

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
        message="Transcript already exists" if is_duplicate else "Transcript uploaded successfully",
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
    List transcripts for the current user.

    Supports filtering by status and filename search.
    """
    service = TranscriptService(db)

    transcripts, total = service.list_transcripts(
        user_id=current_user.id,
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

    transcript = service.get_transcript(transcript_id, current_user.id)

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
    service = TranscriptService(db)

    service.delete_transcript(transcript_id, current_user.id)

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

    transcript = service.get_transcript(transcript_id, current_user.id)

    return BaseResponse(
        success=True,
        data={
            "id": str(transcript.id),
            "filename": transcript.filename,
            "content": transcript.content,
        },
    )
