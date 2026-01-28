"""
Simple per-user rate limiting using Redis.
"""

from typing import Optional

from fastapi import Depends, Request

from app.core.exceptions import RateLimitError
from app.schemas.common import CurrentUser
from app.services.cache_service import CacheService


class RateLimiter:
    """Rate limiter using Redis for tracking request counts."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
            requests_per_hour: Maximum requests allowed per hour
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.cache = CacheService()

    async def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
    ) -> None:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User identifier
            endpoint: API endpoint being accessed

        Raises:
            RateLimitError: If rate limit is exceeded
        """
        minute_key = f"rate_limit:minute:{user_id}:{endpoint}"
        hour_key = f"rate_limit:hour:{user_id}"

        # Check minute limit
        minute_count = self.cache.get(minute_key) or 0
        if int(minute_count) >= self.requests_per_minute:
            raise RateLimitError(
                f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
            )

        # Check hour limit
        hour_count = self.cache.get(hour_key) or 0
        if int(hour_count) >= self.requests_per_hour:
            raise RateLimitError(
                f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
            )

        # Increment counters
        self.cache.increment(minute_key, ttl=60)
        self.cache.increment(hour_key, ttl=3600)


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(
    request: Request,
    current_user: Optional[CurrentUser] = None,
) -> None:
    """
    Dependency to check rate limits for authenticated users.

    Args:
        request: FastAPI request object
        current_user: Optional authenticated user

    Raises:
        RateLimitError: If rate limit is exceeded
    """
    if current_user:
        endpoint = f"{request.method}:{request.url.path}"
        await rate_limiter.check_rate_limit(current_user.id, endpoint)
