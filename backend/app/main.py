"""
FastAPI Application Entry Point.

InsightBoard Dependency Engine - A production-ready backend for
analyzing project transcripts and extracting task dependencies.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.core.logging import setup_logging
from app.middleware.cors import setup_cors
from app.middleware.error_handler import setup_exception_handlers

# Setup logging
logger = setup_logging()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title="InsightBoard Dependency Engine",
        description="""
        A production-ready API for analyzing project transcripts
        and extracting task dependencies using LLM.

        ## Features
        - Upload and parse project transcripts (.txt, .pdf)
        - LLM-powered task and dependency extraction
        - Dependency graph visualization (React Flow compatible)
        - Critical path analysis and bottleneck detection
        - Async job processing with progress tracking
        - Webhook subscriptions for events
        - Export to JSON, CSV, and Gantt formats

        ## Authentication
        All endpoints require a valid Supabase JWT token
        in the Authorization header: `Bearer <token>`
        """,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # Setup middleware
    setup_cors(app)
    setup_exception_handlers(app)

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring."""
        from app.services.cache_service import cache_service

        redis_ok = cache_service.health_check()

        return JSONResponse(
            status_code=200 if redis_ok else 503,
            content={
                "status": "healthy" if redis_ok else "degraded",
                "version": "1.0.0",
                "services": {
                    "redis": "ok" if redis_ok else "unavailable",
                },
            },
        )

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "InsightBoard Dependency Engine",
            "version": "1.0.0",
            "docs": f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
            "health": "/health",
        }

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
