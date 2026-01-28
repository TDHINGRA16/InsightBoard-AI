"""
Main API v1 router - aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1 import (
    analysis,
    analytics,
    dependencies,
    export,
    graphs,
    jobs,
    tasks,
    transcripts,
    webhooks,
)

api_router = APIRouter()

# Include all routers
api_router.include_router(
    transcripts.router,
    prefix="/transcripts",
    tags=["Transcripts"],
)

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"],
)

api_router.include_router(
    dependencies.router,
    prefix="/dependencies",
    tags=["Dependencies"],
)

api_router.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["Analysis"],
)

api_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["Jobs"],
)

api_router.include_router(
    graphs.router,
    prefix="/graphs",
    tags=["Graphs"],
)

api_router.include_router(
    export.router,
    prefix="/export",
    tags=["Export"],
)

api_router.include_router(
    webhooks.router,
    prefix="/webhooks",
    tags=["Webhooks"],
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"],
)
