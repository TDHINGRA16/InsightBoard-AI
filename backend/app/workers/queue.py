"""
RQ Queue and Redis connection factory.
"""

from typing import Optional

import redis
from rq import Queue

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global connection cache
_redis_connection: Optional[redis.Redis] = None
_queue: Optional[Queue] = None


def get_redis_connection() -> redis.Redis:
    """
    Get or create Redis connection for RQ.

    Returns:
        redis.Redis: Redis connection
    """
    global _redis_connection

    if _redis_connection is None:
        _redis_connection = redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,  # RQ needs binary encoding
        )
        logger.info("Redis connection established for RQ")

    return _redis_connection


def get_queue(name: str = "default") -> Queue:
    """
    Get or create an RQ queue.

    Args:
        name: Queue name

    Returns:
        Queue: RQ queue instance
    """
    global _queue

    if _queue is None or _queue.name != name:
        connection = get_redis_connection()
        _queue = Queue(name, connection=connection)
        logger.info(f"RQ queue '{name}' initialized")

    return _queue


def get_high_priority_queue() -> Queue:
    """
    Get high priority queue for urgent jobs.

    Returns:
        Queue: High priority queue
    """
    connection = get_redis_connection()
    return Queue("high", connection=connection)


def get_low_priority_queue() -> Queue:
    """
    Get low priority queue for background jobs.

    Returns:
        Queue: Low priority queue
    """
    connection = get_redis_connection()
    return Queue("low", connection=connection)


def enqueue_job(
    func,
    *args,
    queue_name: str = "default",
    job_id: Optional[str] = None,
    job_timeout: int = 600,
    result_ttl: int = 3600,
    **kwargs,
) -> str:
    """
    Enqueue a job to RQ.

    Args:
        func: Function to execute
        *args: Positional arguments for function
        queue_name: Name of queue to use
        job_id: Optional custom job ID
        job_timeout: Job timeout in seconds
        result_ttl: Result TTL in seconds
        **kwargs: Keyword arguments for function

    Returns:
        str: Job ID
    """
    queue = get_queue(queue_name)

    job = queue.enqueue(
        func,
        *args,
        job_id=job_id,
        job_timeout=job_timeout,
        result_ttl=result_ttl,
        **kwargs,
    )

    logger.info(f"Job enqueued: {job.id} on queue '{queue_name}'")
    return job.id


def get_job_status(job_id: str) -> dict:
    """
    Get status of an RQ job.

    Args:
        job_id: Job ID

    Returns:
        dict: Job status info
    """
    from rq.job import Job

    connection = get_redis_connection()

    try:
        job = Job.fetch(job_id, connection=connection)
        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "error": job.exc_info,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
        }
    except Exception as e:
        logger.error(f"Failed to fetch job {job_id}: {e}")
        return {
            "id": job_id,
            "status": "unknown",
            "error": str(e),
        }
