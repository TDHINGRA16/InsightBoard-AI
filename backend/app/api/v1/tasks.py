"""
Tasks API endpoints.
"""

import math
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from app.core.exceptions import NotFoundError
from app.dependencies import AuthUser, DbSession
from app.models.audit_log import AuditAction, ResourceType
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.dependency import Dependency
from app.models.transcript import Transcript
from app.schemas.common import BaseResponse
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskSingleResponse,
    TaskUpdate,
    TaskWithDependencies,
)
from app.services.audit_service import AuditService
from app.services.webhook_service import trigger_task_completed, trigger_task_created
from app.services.cache_service import cache_service

router = APIRouter()


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks",
)
async def list_tasks(
    transcript_id: Optional[str] = Query(default=None),
    status: Optional[TaskStatus] = Query(default=None),
    priority: Optional[TaskPriority] = Query(default=None),
    assignee: Optional[str] = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    List tasks with filtering and pagination.

    Filter by transcript_id, status, priority, or assignee.
    """
    # Shared workspace: show ALL tasks with eager loading to fix N+1 queries
    query = (
        db.query(Task)
        .join(Transcript)
        .options(
            joinedload(Task.dependencies),
            joinedload(Task.dependents),
        )
    )

    if transcript_id:
        query = query.filter(Task.transcript_id == transcript_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee:
        query = query.filter(Task.assignee.ilike(f"%{assignee}%"))

    # Count
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    tasks = (
        query.order_by(desc(Task.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return TaskListResponse(
        success=True,
        data=[
            TaskResponse(
                id=str(t.id),
                transcript_id=str(t.transcript_id),
                title=t.title,
                description=t.description,
                deadline=t.deadline,
                priority=t.priority,
                status=t.status,
                assignee=t.assignee,
                estimated_hours=t.estimated_hours,
                actual_hours=t.actual_hours,
                position_x=t.position_x or 0,
                position_y=t.position_y or 0,
                created_at=t.created_at,
                updated_at=t.updated_at,
                dependencies_count=len(t.dependencies) if t.dependencies else 0,
                dependents_count=len(t.dependents) if t.dependents else 0,
            )
            for t in tasks
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=TaskSingleResponse,
    summary="Create a task",
)
async def create_task(
    task_data: TaskCreate,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Create a new task manually.

    Task must be associated with a transcript you own.
    """
    # Shared workspace: any user can create tasks for any transcript
    transcript = (
        db.query(Transcript)
        .filter(
            Transcript.id == task_data.transcript_id,
        )
        .first()
    )

    if not transcript:
        raise NotFoundError("Transcript", task_data.transcript_id)

    # Create task
    task = Task(
        transcript_id=task_data.transcript_id,
        title=task_data.title,
        description=task_data.description,
        deadline=task_data.deadline,
        priority=task_data.priority,
        status=task_data.status,
        assignee=task_data.assignee,
        estimated_hours=task_data.estimated_hours,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # Invalidate graph cache
    cache_service.invalidate_graph(str(task.transcript_id))

    # Audit log
    audit_service = AuditService(db)
    audit_service.log_create(
        user_id=current_user.id,
        resource_type=ResourceType.TASK,
        resource_id=str(task.id),
        values={"title": task.title, "transcript_id": str(task.transcript_id)},
    )

    # Trigger webhook
    try:
        trigger_task_created(
            db,
            current_user.id,
            str(task.id),
            task.title,
            str(task.transcript_id),
        )
    except Exception:
        pass

    return TaskSingleResponse(
        success=True,
        data=TaskWithDependencies(
            id=str(task.id),
            transcript_id=str(task.transcript_id),
            title=task.title,
            description=task.description,
            deadline=task.deadline,
            priority=task.priority,
            status=task.status,
            assignee=task.assignee,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            position_x=task.position_x or 0,
            position_y=task.position_y or 0,
            created_at=task.created_at,
            updated_at=task.updated_at,
            dependencies_count=0,
            dependents_count=0,
            dependencies=[],
            dependents=[],
        ),
    )


@router.get(
    "/{task_id}",
    response_model=TaskSingleResponse,
    summary="Get task details",
)
async def get_task(
    task_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get details of a specific task with dependencies.
    """
    task = (
        db.query(Task)
        .options(
            joinedload(Task.dependencies),
            joinedload(Task.dependents),
        )
        .join(Transcript)
        .filter(
            Task.id == task_id,
        )
        .first()
    )

    if not task:
        raise NotFoundError("Task", task_id)

    return TaskSingleResponse(
        success=True,
        data=TaskWithDependencies(
            id=str(task.id),
            transcript_id=str(task.transcript_id),
            title=task.title,
            description=task.description,
            deadline=task.deadline,
            priority=task.priority,
            status=task.status,
            assignee=task.assignee,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            position_x=task.position_x or 0,
            position_y=task.position_y or 0,
            created_at=task.created_at,
            updated_at=task.updated_at,
            dependencies_count=len(task.dependencies),
            dependents_count=len(task.dependents),
            dependencies=[str(d.depends_on_task_id) for d in task.dependencies],
            dependents=[str(d.task_id) for d in task.dependents],
        ),
    )


@router.put(
    "/{task_id}",
    response_model=TaskSingleResponse,
    summary="Update a task",
)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Update a task's properties.
    """
    task = (
        db.query(Task)
        .join(Transcript)
        .filter(
            Task.id == task_id,
        )
        .first()
    )

    if not task:
        raise NotFoundError("Task", task_id)

    # Track old values for audit
    old_status = task.status

    # Update fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.deadline is not None:
        task.deadline = task_data.deadline
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.assignee is not None:
        task.assignee = task_data.assignee
    if task_data.estimated_hours is not None:
        task.estimated_hours = task_data.estimated_hours
    if task_data.actual_hours is not None:
        task.actual_hours = task_data.actual_hours

    db.commit()
    db.refresh(task)

    # Audit log
    audit_service = AuditService(db)
    audit_service.log_update(
        user_id=current_user.id,
        resource_type=ResourceType.TASK,
        resource_id=str(task.id),
        old_values={"status": old_status.value},
        new_values={"status": task.status.value},
    )

    # Trigger webhook if completed
    if task.status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
        try:
            trigger_task_completed(
                db,
                current_user.id,
                str(task.id),
                task.title,
            )
        except Exception:
            pass

    return TaskSingleResponse(
        success=True,
        data=TaskWithDependencies(
            id=str(task.id),
            transcript_id=str(task.transcript_id),
            title=task.title,
            description=task.description,
            deadline=task.deadline,
            priority=task.priority,
            status=task.status,
            assignee=task.assignee,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            position_x=task.position_x or 0,
            position_y=task.position_y or 0,
            created_at=task.created_at,
            updated_at=task.updated_at,
            dependencies_count=len(task.dependencies) if task.dependencies else 0,
            dependents_count=len(task.dependents) if task.dependents else 0,
            dependencies=[],
            dependents=[],
        ),
    )


@router.delete(
    "/{task_id}",
    response_model=BaseResponse,
    summary="Delete a task",
)
async def delete_task(
    task_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Delete a task and its dependencies.
    """
    task = (
        db.query(Task)
        .join(Transcript)
        .filter(
            Task.id == task_id,
        )
        .first()
    )

    if not task:
        raise NotFoundError("Task", task_id)

    # Audit log
    audit_service = AuditService(db)
    audit_service.log_delete(
        user_id=current_user.id,
        resource_type=ResourceType.TASK,
        resource_id=str(task.id),
        old_values={"title": task.title},
    )

    # Capture transcript id before delete for cache invalidation
    transcript_id = str(task.transcript_id)

    db.delete(task)
    db.commit()

    # Invalidate graph cache
    cache_service.invalidate_graph(transcript_id)

    return BaseResponse(
        success=True,
        message="Task deleted successfully",
    )


@router.get(
    "/{task_id}/related",
    response_model=BaseResponse,
    summary="Get tasks related to a task (dependencies + dependents)",
)
async def get_related_tasks(
    task_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Return minimal info about all dependency/dependent tasks for a given task.
    """
    task = (
        db.query(Task)
        .options(
            joinedload(Task.dependencies).joinedload(Dependency.depends_on_task),
            joinedload(Task.dependents).joinedload(Dependency.task),
        )
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise NotFoundError("Task", task_id)

    # Use already-loaded relationships instead of second query
    related_data = []
    
    for dep in task.dependencies:
        if dep.depends_on_task:
            related_data.append({
                "id": str(dep.depends_on_task_id),
                "title": dep.depends_on_task.title,
                "status": dep.depends_on_task.status.value,
            })
    
    for dep in task.dependents:
        if dep.task:
            related_data.append({
                "id": str(dep.task_id),
                "title": dep.task.title,
                "status": dep.task.status.value,
            })
    
    return BaseResponse(success=True, data=related_data)


@router.post(
    "/{task_id}/complete",
    response_model=BaseResponse,
    summary="Mark a task completed",
)
async def complete_task(
    task_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Mark a task completed.

    Backend-side guard: if any blocking dependency isn't completed, refuse.
    """
    task = (
        db.query(Task)
        .options(joinedload(Task.dependencies).joinedload(Dependency.depends_on_task))
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise NotFoundError("Task", task_id)

    # Block if any dependency task isn't completed (use already-loaded relationships)
    if task.dependencies:
        incomplete = [
            d.depends_on_task for d in task.dependencies
            if d.depends_on_task and d.depends_on_task.status != TaskStatus.COMPLETED
        ]
        if incomplete:
            return BaseResponse(
                success=False,
                message="Task is blocked by incomplete dependencies",
                data={"blocked_by": [{"id": str(t.id), "title": t.title} for t in incomplete]},
            )

    if task.status != TaskStatus.COMPLETED:
        old_status = task.status
        task.status = TaskStatus.COMPLETED
        db.commit()
        db.refresh(task)
        # Invalidate graph cache
        cache_service.invalidate_graph(str(task.transcript_id))

        # Audit + webhook
        audit_service = AuditService(db)
        audit_service.log_update(
            user_id=current_user.id,
            resource_type=ResourceType.TASK,
            resource_id=str(task.id),
            old_values={"status": old_status.value},
            new_values={"status": task.status.value},
        )
        try:
            trigger_task_completed(db, current_user.id, str(task.id), task.title)
        except Exception:
            pass

    return BaseResponse(success=True, data={"id": str(task.id), "status": task.status})
