"""Workers module - Background job processing with RQ.

Note: We avoid importing heavy dependencies (e.g., LLM SDKs) at import-time.
Some environments (like local Windows dev) may run tooling that imports
`app.workers` without having all optional runtime deps installed.
"""

from __future__ import annotations

from app.workers.queue import get_queue, get_redis_connection

__all__ = ["get_queue", "get_redis_connection", "analyze_transcript_job", "export_data_job"]


def __getattr__(name: str):
    # Lazy-load task functions to avoid import-time dependency failures.
    if name in {"analyze_transcript_job", "export_data_job"}:
        from app.workers.tasks import analyze_transcript_job, export_data_job

        return {"analyze_transcript_job": analyze_transcript_job, "export_data_job": export_data_job}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
