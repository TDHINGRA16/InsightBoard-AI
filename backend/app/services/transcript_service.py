"""
Transcript service for file handling and storage.
"""

import hashlib
import os
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import (
    DuplicateError,
    FileProcessingError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import get_logger
from app.models.transcript import Transcript, TranscriptStatus
from app.schemas.transcript import TranscriptListItem, TranscriptResponse
from app.utils.file_parser import extract_text_from_file

logger = get_logger(__name__)


class TranscriptService:
    """
    Service for transcript operations.

    Handles file upload, parsing, storage, and retrieval.
    """

    ALLOWED_EXTENSIONS = [".txt", ".pdf"]
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    def __init__(self, db: Session):
        """
        Initialize transcript service.

        Args:
            db: Database session
        """
        self.db = db

    def upload_transcript(
        self,
        user_id: str,
        filename: str,
        file_content: bytes,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[Transcript, bool]:
        """
        Upload and save a transcript.

        Args:
            user_id: UUID of uploading user
            filename: Original filename
            file_content: Raw file bytes
            idempotency_key: Optional key for deduplication

        Returns:
            Tuple[Transcript, bool]: (transcript, is_duplicate)

        Raises:
            ValidationError: If file type or size is invalid
            FileProcessingError: If file parsing fails
        """
        # Validate file extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Invalid file type: {ext}. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Validate file size
        size_bytes = len(file_content)
        if size_bytes > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large: {size_bytes / 1024 / 1024:.1f}MB. Max: {self.MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Extract text content
        text_content = extract_text_from_file(file_content, ext)

        if not text_content or not text_content.strip():
            raise FileProcessingError("File appears to be empty or unreadable", filename)

        # Compute content hash for deduplication
        content_hash = hashlib.sha256(text_content.encode()).hexdigest()

        # Check for duplicate by content hash (GLOBAL - shared workspace)
        existing = self.db.query(Transcript).filter(Transcript.content_hash == content_hash).first()

        if existing:
            logger.info(f"Duplicate transcript detected: {existing.id}")
            return existing, True

        # Create new transcript
        transcript = Transcript(
            user_id=user_id,
            filename=filename,
            file_type=ext,
            size_bytes=size_bytes,
            content=text_content,
            content_hash=content_hash,
            status=TranscriptStatus.UPLOADED,
        )

        self.db.add(transcript)
        self.db.commit()
        self.db.refresh(transcript)

        logger.info(f"Transcript uploaded: {transcript.id}")
        return transcript, False

    def get_transcript(self, transcript_id: str) -> Transcript:
        """
        Get a transcript by ID.

        Args:
            transcript_id: UUID of transcript
            user_id: UUID of requesting user

        Returns:
            Transcript: The transcript

        Raises:
            NotFoundError: If transcript not found or not owned by user
        """
        transcript = (
            self.db.query(Transcript)
            .options(joinedload(Transcript.tasks))
            .filter(Transcript.id == transcript_id)
            .first()
        )

        if not transcript:
            raise NotFoundError("Transcript", transcript_id)

        return transcript

    def list_transcripts(
        self,
        status: Optional[TranscriptStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Transcript], int]:
        """
        List transcripts for a user with pagination.

        Args:
            user_id: UUID of user
            status: Optional status filter
            search: Optional filename search
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple[List[Transcript], int]: (transcripts, total_count)
        """
        # Shared workspace: list ALL transcripts with eager loading to fix N+1 queries
        query = self.db.query(Transcript)
        query = query.options(joinedload(Transcript.tasks))

        if status:
            query = query.filter(Transcript.status == status)

        if search:
            query = query.filter(Transcript.filename.ilike(f"%{search}%"))

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        transcripts = (
            query.order_by(desc(Transcript.created_at))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return transcripts, total

    def delete_transcript(
        self,
        transcript_id: str,
    ) -> bool:
        """
        Delete a transcript.

        Args:
            transcript_id: UUID of transcript
            user_id: UUID of requesting user

        Returns:
            bool: True if deleted

        Raises:
            NotFoundError: If transcript not found
        """
        transcript = self.get_transcript(transcript_id)

        self.db.delete(transcript)
        self.db.commit()

        logger.info(f"Transcript deleted: {transcript_id}")
        return True

    def update_status(
        self,
        transcript_id: str,
        status: TranscriptStatus,
        error_message: Optional[str] = None,
        analysis_result: Optional[dict] = None,
    ) -> Transcript:
        """
        Update transcript status.

        Args:
            transcript_id: UUID of transcript
            status: New status
            error_message: Optional error message
            analysis_result: Optional analysis result data

        Returns:
            Transcript: Updated transcript
        """
        transcript = (
            self.db.query(Transcript)
            .filter(Transcript.id == transcript_id)
            .first()
        )

        if not transcript:
            raise NotFoundError("Transcript", transcript_id)

        transcript.status = status
        if error_message:
            transcript.error_message = error_message
        if analysis_result:
            transcript.analysis_result = analysis_result

        self.db.commit()
        self.db.refresh(transcript)

        return transcript

    def get_transcript_with_task_count(
        self,
        transcript_id: str,
    ) -> dict:
        """
        Get transcript with task count for response.

        Args:
            transcript_id: UUID of transcript
            user_id: UUID of user

        Returns:
            dict: Transcript data with task_count
        """
        transcript = self.get_transcript(transcript_id)
        task_count = len(transcript.tasks) if transcript.tasks else 0

        return {
            **transcript.__dict__,
            "task_count": task_count,
        }
