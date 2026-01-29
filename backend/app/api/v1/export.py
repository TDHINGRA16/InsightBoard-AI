"""
Export API endpoints - Export data in various formats.
"""

from fastapi import APIRouter
from fastapi.responses import Response

from app.core.exceptions import NotFoundError
from app.dependencies import AuthUser, DbSession
from app.models.transcript import Transcript
from app.schemas.export import ExportFormat, ExportRequest, ExportResponse
from app.services.export_service import ExportService

router = APIRouter()


@router.post(
    "",
    response_model=ExportResponse,
    summary="Export transcript data",
)
async def export_data(
    request: ExportRequest,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Export transcript tasks and dependencies in requested format.

    Supported formats: json, csv, gantt
    """
    # Shared workspace: verify transcript exists
    transcript = (
        db.query(Transcript)
        .filter(Transcript.id == request.transcript_id)
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", request.transcript_id)

    service = ExportService(db)

    result = service.export_transcript(
        transcript_id=request.transcript_id,
        user_id=current_user.id,
        format=request.format,
        include_dependencies=request.include_dependencies,
        include_graph=request.include_graph,
    )

    return ExportResponse(
        success=True,
        format=request.format,
        data=result["data"],
        filename=result["filename"],
        content_type=result["content_type"],
    )


@router.get(
    "/{transcript_id}/json",
    summary="Export as JSON",
)
async def export_json(
    transcript_id: str,
    include_graph: bool = False,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Export transcript data as JSON.

    Returns inline JSON data.
    """
    # Shared workspace: any user can export any transcript
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == transcript_id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", transcript_id)

    service = ExportService(db)

    result = service.export_transcript(
        transcript_id=transcript_id,
        user_id=current_user.id,
        format=ExportFormat.JSON,
        include_dependencies=True,
        include_graph=include_graph,
    )

    return result["data"]


@router.get(
    "/{transcript_id}/csv",
    summary="Export as CSV",
)
async def export_csv(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Export transcript tasks as CSV.

    Returns CSV file for download.
    """
    # Shared workspace: any user can export any transcript
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == transcript_id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", transcript_id)

    service = ExportService(db)

    result = service.export_transcript(
        transcript_id=transcript_id,
        user_id=current_user.id,
        format=ExportFormat.CSV,
        include_dependencies=True,
        include_graph=False,
    )

    return Response(
        content=result["data"],
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{result["filename"]}"'
        },
    )


@router.get(
    "/{transcript_id}/gantt",
    summary="Export as Gantt",
)
async def export_gantt(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Export transcript as Gantt chart data.

    Returns JSON data compatible with Gantt chart libraries.
    """
    # Shared workspace: any user can export any transcript
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == transcript_id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", transcript_id)

    service = ExportService(db)

    result = service.export_transcript(
        transcript_id=transcript_id,
        user_id=current_user.id,
        format=ExportFormat.GANTT,
        include_dependencies=True,
        include_graph=False,
    )

    return result["data"]
