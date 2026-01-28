"""
Webhook schemas for event subscriptions.
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.webhook import WebhookEventType


class WebhookBase(BaseModel):
    """Base webhook fields."""

    event_type: WebhookEventType
    endpoint_url: str = Field(..., description="URL to receive webhook POSTs")
    description: Optional[str] = Field(default=None, max_length=255)


class WebhookCreate(WebhookBase):
    """Request schema for creating a webhook."""

    pass


class WebhookUpdate(BaseModel):
    """Request schema for updating a webhook."""

    endpoint_url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(WebhookBase):
    """Single webhook response."""

    id: str
    user_id: str
    is_active: bool
    secret_key: str = Field(description="HMAC signing key for verification")
    failed_attempts: int
    last_triggered_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookListItem(BaseModel):
    """Webhook item for list responses (excludes secret)."""

    id: str
    event_type: WebhookEventType
    endpoint_url: str
    is_active: bool
    failed_attempts: int
    last_triggered_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookListResponse(BaseModel):
    """List of webhooks response."""

    success: bool = True
    data: List[WebhookListItem]
    total: int


class WebhookPayload(BaseModel):
    """Payload sent to webhook endpoints."""

    event_type: str
    timestamp: str
    data: Any


class WebhookTestRequest(BaseModel):
    """Request to test a webhook."""

    webhook_id: str


class WebhookTestResponse(BaseModel):
    """Response from webhook test."""

    success: bool
    message: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
