"""
Redis cache service for caching analysis results and rate limiting.
"""

import json
from typing import Any, Optional

import redis

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Redis-based caching service.

    Provides generic caching and specific helpers for analysis caching.
    """

    def __init__(self):
        """Initialize Redis connection."""
        self._redis: Optional[redis.Redis] = None

    @property
    def redis(self) -> redis.Redis:
        """
        Lazy-load Redis connection.

        Returns:
            redis.Redis: Redis client instance
        """
        if self._redis is None:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self._redis

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
    ) -> bool:
        """
        Set a cache value with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if not string)
            ttl: Time-to-live in seconds

        Returns:
            bool: True if set successfully
        """
        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            self.redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Get a cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a cached value.

        Args:
            key: Cache key

        Returns:
            bool: True if deleted
        """
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def increment(self, key: str, ttl: int = 60) -> int:
        """
        Increment a counter with TTL.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds

        Returns:
            int: New counter value
        """
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = pipe.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0

    def cache_analysis(
        self,
        transcript_id: str,
        analysis_data: dict,
        ttl: int = None,
    ) -> bool:
        """
        Cache analysis results for a transcript.

        Args:
            transcript_id: UUID of transcript
            analysis_data: Analysis result data
            ttl: Override default TTL

        Returns:
            bool: True if cached successfully
        """
        key = f"analysis:{transcript_id}"
        return self.set(key, analysis_data, ttl or settings.ANALYSIS_CACHE_TTL)

    def get_cached_analysis(self, transcript_id: str) -> Optional[dict]:
        """
        Get cached analysis for a transcript.

        Args:
            transcript_id: UUID of transcript

        Returns:
            Cached analysis data or None
        """
        key = f"analysis:{transcript_id}"
        return self.get(key)

    def invalidate_analysis(self, transcript_id: str) -> bool:
        """
        Invalidate cached analysis for a transcript.

        Args:
            transcript_id: UUID of transcript

        Returns:
            bool: True if invalidated
        """
        key = f"analysis:{transcript_id}"
        return self.delete(key)

    def cache_graph(
        self,
        transcript_id: str,
        graph_data: dict,
        ttl: int = None,
    ) -> bool:
        """
        Cache graph data for a transcript.

        Args:
            transcript_id: UUID of transcript
            graph_data: React Flow graph data
            ttl: Override default TTL

        Returns:
            bool: True if cached successfully
        """
        key = f"graph:{transcript_id}"
        return self.set(key, graph_data, ttl or settings.ANALYSIS_CACHE_TTL)

    def get_cached_graph(self, transcript_id: str) -> Optional[dict]:
        """
        Get cached graph for a transcript.

        Args:
            transcript_id: UUID of transcript

        Returns:
            Cached graph data or None
        """
        key = f"graph:{transcript_id}"
        return self.get(key)

    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.

        Returns:
            bool: True if connection is healthy
        """
        try:
            self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Singleton instance
cache_service = CacheService()
