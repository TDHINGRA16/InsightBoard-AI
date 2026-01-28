"""
Webhooks API endpoints - Manage webhook subscriptions.
"""

from typing import Optional

from fastapi import APIRouter, Query

from app.core.exceptions import NotFoundError
from app.dependencies import AuthUser, DbSession
from app.models.audit_log import AuditAction, ResourceType
from app.models.webhook import Webhook, WebhookEventType
from app.schemas.common import BaseResponse
from app.schemas.webhook import (
    WebhookCreate,
    WebhookListResponse,
    WebhookResponse,
    WebhookTestResponse,
    WebhookUpdate,
)
from app.services.audit_service import AuditService
from app.services.webhook_service import WebhookService

router = APIRouter()


@router.get(
    "",
    response_model=WebhookListResponse,
    summary="List webhooks",
)
async def list_webhooks(
    event_type: Optional[WebhookEventType] = Query(default=None),
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    List all webhook subscriptions for the current user.
    """
    service = WebhookService(db)

    webhooks = service.get_webhooks(
        user_id=current_user.id,
        event_type=event_type,
    )

    return WebhookListResponse(
        success=True,
        data=[
            {
                "id": str(w.id),
                "event_type": w.event_type,
                "endpoint_url": w.endpoint_url,
                "is_active": w.is_active,
                "failed_attempts": w.failed_attempts,
                "last_triggered_at": w.last_triggered_at,
                "created_at": w.created_at,
            }
            for w in webhooks
        ],
        total=len(webhooks),
    )


@router.post(
    "",
    response_model=BaseResponse,
    summary="Create webhook",
)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Create a new webhook subscription.

    Webhooks will receive POST requests when the specified event occurs.
    Payloads are signed with HMAC-SHA256 using the returned secret_key.
    """
    service = WebhookService(db)

    webhook = service.create_webhook(
        user_id=current_user.id,
        event_type=webhook_data.event_type,
        endpoint_url=webhook_data.endpoint_url,
        description=webhook_data.description,
    )

    # Audit log
    audit_service = AuditService(db)
    audit_service.log_create(
        user_id=current_user.id,
        resource_type=ResourceType.WEBHOOK,
        resource_id=str(webhook.id),
        values={
            "event_type": webhook.event_type.value,
            "endpoint_url": webhook.endpoint_url,
        },
    )

    return BaseResponse(
        success=True,
        data=WebhookResponse(
            id=str(webhook.id),
            user_id=str(webhook.user_id),
            event_type=webhook.event_type,
            endpoint_url=webhook.endpoint_url,
            description=webhook.description,
            is_active=webhook.is_active,
            secret_key=webhook.secret_key,
            failed_attempts=webhook.failed_attempts,
            last_triggered_at=webhook.last_triggered_at,
            created_at=webhook.created_at,
        ),
        message="Webhook created successfully",
    )


@router.get(
    "/{webhook_id}",
    response_model=BaseResponse,
    summary="Get webhook details",
)
async def get_webhook(
    webhook_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Get details of a specific webhook including secret key.
    """
    webhook = (
        db.query(Webhook)
        .filter(
            Webhook.id == webhook_id,
            Webhook.user_id == current_user.id,
        )
        .first()
    )

    if not webhook:
        raise NotFoundError("Webhook", webhook_id)

    return BaseResponse(
        success=True,
        data=WebhookResponse(
            id=str(webhook.id),
            user_id=str(webhook.user_id),
            event_type=webhook.event_type,
            endpoint_url=webhook.endpoint_url,
            description=webhook.description,
            is_active=webhook.is_active,
            secret_key=webhook.secret_key,
            failed_attempts=webhook.failed_attempts,
            last_triggered_at=webhook.last_triggered_at,
            last_error=webhook.last_error,
            created_at=webhook.created_at,
        ),
    )


@router.patch(
    "/{webhook_id}",
    response_model=BaseResponse,
    summary="Update webhook",
)
async def update_webhook(
    webhook_id: str,
    webhook_data: WebhookUpdate,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Update a webhook's URL, description, or active status.
    """
    webhook = (
        db.query(Webhook)
        .filter(
            Webhook.id == webhook_id,
            Webhook.user_id == current_user.id,
        )
        .first()
    )

    if not webhook:
        raise NotFoundError("Webhook", webhook_id)

    if webhook_data.endpoint_url is not None:
        webhook.endpoint_url = webhook_data.endpoint_url
    if webhook_data.description is not None:
        webhook.description = webhook_data.description
    if webhook_data.is_active is not None:
        webhook.is_active = webhook_data.is_active

    db.commit()
    db.refresh(webhook)

    return BaseResponse(
        success=True,
        data=WebhookResponse(
            id=str(webhook.id),
            user_id=str(webhook.user_id),
            event_type=webhook.event_type,
            endpoint_url=webhook.endpoint_url,
            description=webhook.description,
            is_active=webhook.is_active,
            secret_key=webhook.secret_key,
            failed_attempts=webhook.failed_attempts,
            last_triggered_at=webhook.last_triggered_at,
            created_at=webhook.created_at,
        ),
        message="Webhook updated successfully",
    )


@router.delete(
    "/{webhook_id}",
    response_model=BaseResponse,
    summary="Delete webhook",
)
async def delete_webhook(
    webhook_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Delete a webhook subscription.
    """
    service = WebhookService(db)

    deleted = service.delete_webhook(webhook_id, current_user.id)

    if not deleted:
        raise NotFoundError("Webhook", webhook_id)

    # Audit log
    audit_service = AuditService(db)
    audit_service.log_delete(
        user_id=current_user.id,
        resource_type=ResourceType.WEBHOOK,
        resource_id=webhook_id,
        old_values={},
    )

    return BaseResponse(
        success=True,
        message="Webhook deleted successfully",
    )


@router.post(
    "/{webhook_id}/test",
    response_model=WebhookTestResponse,
    summary="Test webhook",
)
async def test_webhook(
    webhook_id: str,
    db: DbSession = None,
    current_user: AuthUser = None,
):
    """
    Send a test payload to a webhook to verify it's working.
    """
    service = WebhookService(db)

    result = service.test_webhook(webhook_id, current_user.id)

    return WebhookTestResponse(
        success=result.get("success", False),
        message=result.get("message", "Test completed"),
        status_code=result.get("status_code"),
        response_time_ms=result.get("response_time_ms"),
    )


@router.get(
    "/events",
    summary="List available event types",
)
async def list_event_types():
    """
    List all available webhook event types.
    """
    return {
        "success": True,
        "data": [
            {
                "type": event.value,
                "description": _get_event_description(event),
            }
            for event in WebhookEventType
        ],
    }


def _get_event_description(event: WebhookEventType) -> str:
    """Get description for event type."""
    descriptions = {
        WebhookEventType.ANALYSIS_COMPLETED: "Triggered when transcript analysis completes successfully",
        WebhookEventType.ANALYSIS_FAILED: "Triggered when transcript analysis fails",
        WebhookEventType.TASK_CREATED: "Triggered when a new task is created",
        WebhookEventType.TASK_UPDATED: "Triggered when a task is updated",
        WebhookEventType.TASK_COMPLETED: "Triggered when a task status changes to completed",
        WebhookEventType.EXPORT_COMPLETED: "Triggered when data export completes",
    }
    return descriptions.get(event, "No description available")
