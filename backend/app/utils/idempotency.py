"""
Idempotency utilities for preventing duplicate operations.
"""

import hashlib
import uuid
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.job import Job

logger = get_logger(__name__)


def generate_idempotency_key(
    user_id: str,
    operation: str,
    *args,
) -> str:
    """
    Generate an idempotency key for an operation.

    Args:
        user_id: UUID of user
        operation: Operation type (e.g., 'upload', 'analyze')
        *args: Additional values to include in key

    Returns:
        str: Idempotency key
    """
    # Combine all inputs
    combined = f"{user_id}:{operation}:{':'.join(str(a) for a in args)}"

    # Hash to fixed length
    return hashlib.sha256(combined.encode()).hexdigest()[:32]


def generate_content_based_key(
    user_id: str,
    content_hash: str,
    operation: str,
) -> str:
    """
    Generate idempotency key based on content hash.

    Args:
        user_id: UUID of user
        content_hash: SHA-256 hash of content
        operation: Operation type

    Returns:
        str: Idempotency key
    """
    combined = f"{user_id}:{content_hash}:{operation}"
    return hashlib.sha256(combined.encode()).hexdigest()[:32]


def check_idempotency(
    db: Session,
    idempotency_key: str,
) -> Tuple[bool, Optional[Job]]:
    """
    Check if an operation with this idempotency key already exists.

    Args:
        db: Database session
        idempotency_key: Key to check

    Returns:
        Tuple[bool, Optional[Job]]: (exists, existing_job)
    """
    existing_job = (
        db.query(Job)
        .filter(Job.idempotency_key == idempotency_key)
        .first()
    )

    if existing_job:
        logger.info(f"Idempotent request detected: {idempotency_key}")
        return True, existing_job

    return False, None


def generate_job_id(
    prefix: str,
    transcript_id: str,
) -> str:
    """
    Generate a unique job ID.

    Args:
        prefix: Job type prefix (e.g., 'analyze', 'export')
        transcript_id: UUID of transcript

    Returns:
        str: Unique job ID
    """
    unique = str(uuid.uuid4())[:8]
    return f"{prefix}-{transcript_id}-{unique}"


class IdempotencyManager:
    """
    Manager for handling idempotent operations.
    """

    def __init__(self, db: Session):
        """
        Initialize idempotency manager.

        Args:
            db: Database session
        """
        self.db = db

    def get_or_create_job(
        self,
        idempotency_key: str,
        job_creator,
    ) -> Tuple[Job, bool]:
        """
        Get existing job or create new one atomically.

        Args:
            idempotency_key: Unique key for operation
            job_creator: Callable that creates a new Job

        Returns:
            Tuple[Job, bool]: (job, is_existing)
        """
        # Check for existing
        exists, existing_job = check_idempotency(self.db, idempotency_key)

        if exists and existing_job:
            return existing_job, True

        # Create new job
        new_job = job_creator()
        new_job.idempotency_key = idempotency_key

        self.db.add(new_job)
        self.db.commit()
        self.db.refresh(new_job)

        return new_job, False
