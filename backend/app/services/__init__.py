"""Services module - Business logic layer.

Keep imports lightweight: some services have optional heavy dependencies.
"""

from __future__ import annotations

from app.services.audit_service import AuditService
from app.services.cache_service import CacheService
from app.services.dependency_service import DependencyService
from app.services.export_service import ExportService
from app.services.graph_service import GraphService
from app.services.transcript_service import TranscriptService
from app.services.webhook_service import WebhookService

__all__ = ["TranscriptService", "NLPService", "DependencyService", "GraphService", "CacheService", "ExportService", "WebhookService", "AuditService"]


def __getattr__(name: str):
    # Lazy-load NLPService to avoid import-time dependency failures (e.g., groq).
    if name == "NLPService":
        from app.services.nlp_service import NLPService

        return NLPService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
