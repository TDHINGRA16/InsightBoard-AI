"""
Dependencies API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Query

from app.core.exceptions import NotFoundError
from app.dependencies import AuthUser, DbSession
from app.models.audit_log import AuditAction, ResourceType
from app.models.dependency import DependencyType
from app.models.task import Task
from app.models.transcript import Transcript
from app.schemas.common import BaseResponse
from app.schemas.dependency import (
    DependencyCreate,
    DependencyListResponse,
    DependencyResponse,
    DependencyValidationResponse,
    TaskDependenciesResponse,
)
from app.services.audit_service import AuditService
from app.services.dependency_service import DependencyService

router = APIRouter()


@router.get(
    "",
    response_model=DependencyListResponse,
    summary="List dependencies",
)
async def list_dependencies(
    transcript_id: Optional[str] = Query(default=None),
    task_id: Optional[str] = Query(default=None),
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    List dependencies with optional filtering.

    Filter by transcript_id or task_id.
    """
    service = DependencyService(db)

    if transcript_id:
        # Shared workspace: any user can view transcript dependencies
        dependencies = service.list_dependencies_for_transcript(transcript_id)
    elif task_id:
        # Shared workspace: any user can view task dependencies
        deps, dependents = service.get_task_dependencies(task_id)
        dependencies = deps + dependents
    else:
        # Default: list ALL dependencies
        from sqlalchemy.orm import joinedload
        from app.models.dependency import Dependency

        dependencies = (
            db.query(Dependency)
            .options(joinedload(Dependency.task), joinedload(Dependency.depends_on_task))
            .all()
        )

    return DependencyListResponse(
        success=True,
        data=[
            DependencyResponse(
                id=str(d.id),
                task_id=str(d.task_id),
                depends_on_task_id=str(d.depends_on_task_id),
                dependency_type=d.dependency_type,
                lag_days=d.lag_days,
                created_at=d.created_at,
                task_title=d.task.title if d.task else None,
                depends_on_title=d.depends_on_task.title if d.depends_on_task else None,
            )
            for d in dependencies
        ],
        total=len(dependencies),
    )


@router.post(
    "",
    response_model=BaseResponse,
    summary="Create a dependency",
)
async def create_dependency(
    dep_data: DependencyCreate,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Create a new dependency between tasks.

    The dependency will be validated to ensure no cycles are created.
    """
    # Shared workspace: any user can create dependencies
    task = (
        db.query(Task)
        .filter(
            Task.id == dep_data.task_id,
        )
        .first()
    )

    if not task:
        raise NotFoundError("Task", dep_data.task_id)

    service = DependencyService(db)

    dependency = service.create_dependency(
        task_id=dep_data.task_id,
        depends_on_task_id=dep_data.depends_on_task_id,
        dependency_type=dep_data.dependency_type,
        lag_days=dep_data.lag_days,
        validate_dag=True,
    )

    # Audit log
    audit_service = AuditService(db)
    audit_service.log_create(
        user_id=current_user.id,
        resource_type=ResourceType.DEPENDENCY,
        resource_id=str(dependency.id),
        values={
            "task_id": str(dependency.task_id),
            "depends_on_task_id": str(dependency.depends_on_task_id),
        },
    )

    return BaseResponse(
        success=True,
        data=DependencyResponse(
            id=str(dependency.id),
            task_id=str(dependency.task_id),
            depends_on_task_id=str(dependency.depends_on_task_id),
            dependency_type=dependency.dependency_type,
            lag_days=dependency.lag_days,
            created_at=dependency.created_at,
        ),
        message="Dependency created successfully",
    )


@router.delete(
    "/{dependency_id}",
    response_model=BaseResponse,
    summary="Delete a dependency",
)
async def delete_dependency(
    dependency_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Delete a dependency.
    """
    from app.models.dependency import Dependency

    # Shared workspace: any user can delete dependencies
    dependency = (
        db.query(Dependency)
        .filter(
            Dependency.id == dependency_id,
        )
        .first()
    )

    if not dependency:
        raise NotFoundError("Dependency", dependency_id)

    service = DependencyService(db)
    service.delete_dependency(dependency_id)

    # Audit log
    audit_service = AuditService(db)
    audit_service.log_delete(
        user_id=current_user.id,
        resource_type=ResourceType.DEPENDENCY,
        resource_id=dependency_id,
        old_values={},
    )

    return BaseResponse(
        success=True,
        message="Dependency deleted successfully",
    )


@router.get(
    "/task/{task_id}",
    response_model=TaskDependenciesResponse,
    summary="Get task dependencies",
)
async def get_task_dependencies(
    task_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get all dependencies and dependents for a task.
    """
    # Shared workspace: any user can view task dependencies
    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
        )
        .first()
    )

    if not task:
        raise NotFoundError("Task", task_id)

    service = DependencyService(db)
    dependencies, dependents = service.get_task_dependencies(task_id)

    return TaskDependenciesResponse(
        success=True,
        task_id=str(task.id),
        task_title=task.title,
        dependencies=[
            DependencyResponse(
                id=str(d.id),
                task_id=str(d.task_id),
                depends_on_task_id=str(d.depends_on_task_id),
                dependency_type=d.dependency_type,
                lag_days=d.lag_days,
                created_at=d.created_at,
                depends_on_title=d.depends_on_task.title if d.depends_on_task else None,
            )
            for d in dependencies
        ],
        dependents=[
            DependencyResponse(
                id=str(d.id),
                task_id=str(d.task_id),
                depends_on_task_id=str(d.depends_on_task_id),
                dependency_type=d.dependency_type,
                lag_days=d.lag_days,
                created_at=d.created_at,
                task_title=d.task.title if d.task else None,
            )
            for d in dependents
        ],
    )


@router.get(
    "/validate/{transcript_id}",
    response_model=DependencyValidationResponse,
    summary="Validate DAG",
)
async def validate_dag(
    transcript_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Validate that the dependency graph is a valid DAG (no cycles).
    """
    # Shared workspace: any user can validate transcript DAG
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == transcript_id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", transcript_id)

    service = DependencyService(db)
    is_valid, cycle = service.validate_dag(transcript_id)

    return DependencyValidationResponse(
        success=True,
        is_valid=is_valid,
        message="Graph is a valid DAG" if is_valid else "Circular dependency detected",
        cycle_detected=cycle,
    )
