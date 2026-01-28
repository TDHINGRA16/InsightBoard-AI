"""
Webhook service for event delivery and management.
"""

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.webhook import Webhook, WebhookEventType

logger = get_logger(__name__)


class WebhookService:
    """
    Service for webhook management and event delivery.

    Handles webhook CRUD and event triggering with HMAC signing.
    """

    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 10

    def __init__(self, db: Session):
        """
        Initialize webhook service.

        Args:
            db: Database session
        """
        self.db = db

    def create_webhook(
        self,
        user_id: str,
        event_type: WebhookEventType,
        endpoint_url: str,
        description: Optional[str] = None,
    ) -> Webhook:
        """
        Create a new webhook subscription.

        Args:
            user_id: UUID of user
            event_type: Event type to subscribe to
            endpoint_url: URL to receive webhook POSTs
            description: Optional description

        Returns:
            Webhook: Created webhook
        """
        webhook = Webhook(
            user_id=user_id,
            event_type=event_type,
            endpoint_url=endpoint_url,
            description=description,
            is_active=True,
        )

        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)

        logger.info(f"Created webhook: {webhook.id} for event {event_type}")
        return webhook

    def get_webhooks(
        self,
        user_id: str,
        event_type: Optional[WebhookEventType] = None,
    ) -> List[Webhook]:
        """
        Get webhooks for a user.

        Args:
            user_id: UUID of user
            event_type: Optional event type filter

        Returns:
            List[Webhook]: User's webhooks
        """
        query = self.db.query(Webhook).filter(Webhook.user_id == user_id)

        if event_type:
            query = query.filter(Webhook.event_type == event_type)

        return query.order_by(Webhook.created_at.desc()).all()

    def delete_webhook(self, webhook_id: str, user_id: str) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: UUID of webhook
            user_id: UUID of user (for authorization)

        Returns:
            bool: True if deleted
        """
        webhook = (
            self.db.query(Webhook)
            .filter(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id,
            )
            .first()
        )

        if not webhook:
            return False

        self.db.delete(webhook)
        self.db.commit()

        logger.info(f"Deleted webhook: {webhook_id}")
        return True

    def toggle_webhook(
        self,
        webhook_id: str,
        user_id: str,
        is_active: bool,
    ) -> Optional[Webhook]:
        """
        Enable or disable a webhook.

        Args:
            webhook_id: UUID of webhook
            user_id: UUID of user
            is_active: New active state

        Returns:
            Optional[Webhook]: Updated webhook or None
        """
        webhook = (
            self.db.query(Webhook)
            .filter(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id,
            )
            .first()
        )

        if not webhook:
            return None

        webhook.is_active = is_active
        self.db.commit()
        self.db.refresh(webhook)

        return webhook

    def trigger_event(
        self,
        event_type: WebhookEventType,
        user_id: str,
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Trigger webhooks for an event.

        Args:
            event_type: Type of event
            user_id: UUID of user (to find their webhooks)
            payload: Event payload data

        Returns:
            List of delivery results
        """
        # Get active webhooks for this event
        webhooks = (
            self.db.query(Webhook)
            .filter(
                Webhook.user_id == user_id,
                Webhook.event_type == event_type,
                Webhook.is_active == True,
            )
            .all()
        )

        if not webhooks:
            logger.debug(f"No webhooks registered for event {event_type}")
            return []

        results = []
        for webhook in webhooks:
            result = self._deliver_webhook(webhook, event_type, payload)
            results.append(result)

        return results

    def _deliver_webhook(
        self,
        webhook: Webhook,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Deliver a webhook with retries and HMAC signing.

        Args:
            webhook: Webhook to deliver to
            event_type: Event type
            payload: Event payload

        Returns:
            Dict with delivery result
        """
        # Build full payload
        full_payload = {
            "event_type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload,
        }

        payload_json = json.dumps(full_payload, default=str)

        # Sign payload with HMAC
        signature = hmac.new(
            webhook.secret_key.encode(),
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Event": event_type.value,
        }

        # Attempt delivery with retries
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                with httpx.Client(timeout=self.TIMEOUT_SECONDS) as client:
                    response = client.post(
                        webhook.endpoint_url,
                        content=payload_json,
                        headers=headers,
                    )

                if response.status_code < 300:
                    # Success
                    webhook.last_triggered_at = datetime.utcnow()
                    webhook.failed_attempts = 0
                    webhook.last_error = None
                    self.db.commit()

                    logger.info(
                        f"Webhook delivered: {webhook.id} to {webhook.endpoint_url}"
                    )

                    return {
                        "webhook_id": str(webhook.id),
                        "success": True,
                        "status_code": response.status_code,
                    }
                else:
                    last_error = f"HTTP {response.status_code}"

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Webhook delivery attempt {attempt + 1} failed: {e}"
                )

        # All retries failed
        webhook.failed_attempts += 1
        webhook.last_error = last_error
        webhook.last_triggered_at = datetime.utcnow()

        # Disable webhook after too many failures
        if webhook.failed_attempts >= 10:
            webhook.is_active = False
            logger.warning(
                f"Webhook {webhook.id} disabled after {webhook.failed_attempts} failures"
            )

        self.db.commit()

        return {
            "webhook_id": str(webhook.id),
            "success": False,
            "error": last_error,
        }

    def test_webhook(
        self,
        webhook_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Send a test payload to a webhook.

        Args:
            webhook_id: UUID of webhook
            user_id: UUID of user

        Returns:
            Dict with test result
        """
        webhook = (
            self.db.query(Webhook)
            .filter(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id,
            )
            .first()
        )

        if not webhook:
            return {
                "success": False,
                "message": "Webhook not found",
            }

        test_payload = {
            "test": True,
            "message": "This is a test webhook delivery from InsightBoard",
            "webhook_id": str(webhook.id),
        }

        start_time = datetime.utcnow()
        result = self._deliver_webhook(webhook, webhook.event_type, test_payload)
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        result["response_time_ms"] = round(elapsed_ms, 2)
        result["message"] = "Test delivery successful" if result["success"] else "Test delivery failed"

        return result


# Event trigger helper functions
def trigger_analysis_completed(
    db: Session,
    user_id: str,
    transcript_id: str,
    task_count: int,
    dependency_count: int,
) -> None:
    """Trigger analysis.completed webhook."""
    service = WebhookService(db)
    service.trigger_event(
        WebhookEventType.ANALYSIS_COMPLETED,
        user_id,
        {
            "transcript_id": transcript_id,
            "task_count": task_count,
            "dependency_count": dependency_count,
        },
    )


def trigger_task_created(
    db: Session,
    user_id: str,
    task_id: str,
    task_title: str,
    transcript_id: str,
) -> None:
    """Trigger task.created webhook."""
    service = WebhookService(db)
    service.trigger_event(
        WebhookEventType.TASK_CREATED,
        user_id,
        {
            "task_id": task_id,
            "task_title": task_title,
            "transcript_id": transcript_id,
        },
    )


def trigger_task_completed(
    db: Session,
    user_id: str,
    task_id: str,
    task_title: str,
) -> None:
    """Trigger task.completed webhook."""
    service = WebhookService(db)
    service.trigger_event(
        WebhookEventType.TASK_COMPLETED,
        user_id,
        {
            "task_id": task_id,
            "task_title": task_title,
        },
    )
