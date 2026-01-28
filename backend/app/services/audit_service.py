"""
Audit service for tracking resource changes.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.audit_log import AuditAction, AuditLog, ResourceType

logger = get_logger(__name__)


class AuditService:
    """
    Service for creating audit log entries.

    Tracks all changes to resources for compliance and debugging.
    """

    def __init__(self, db: Session):
        """
        Initialize audit service.

        Args:
            db: Database session
        """
        self.db = db

    def log(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: ResourceType,
        resource_id: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            user_id: UUID of user performing action
            action: Type of action (created, updated, deleted)
            resource_type: Type of resource
            resource_id: ID of resource
            old_values: Previous values (for updates/deletes)
            new_values: New values (for creates/updates)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            AuditLog: Created audit entry
        """
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(entry)
        self.db.commit()

        logger.debug(
            f"Audit: {action.value} {resource_type.value} {resource_id} by {user_id}"
        )

        return entry

    def log_create(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        values: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a resource creation."""
        return self.log(
            user_id=user_id,
            action=AuditAction.CREATED,
            resource_type=resource_type,
            resource_id=resource_id,
            new_values=values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_update(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a resource update."""
        return self.log(
            user_id=user_id,
            action=AuditAction.UPDATED,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_delete(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        old_values: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a resource deletion."""
        return self.log(
            user_id=user_id,
            action=AuditAction.DELETED,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def get_resource_history(
        self,
        resource_type: ResourceType,
        resource_id: str,
        limit: int = 50,
    ) -> List[AuditLog]:
        """
        Get audit history for a resource.

        Args:
            resource_type: Type of resource
            resource_id: ID of resource
            limit: Maximum entries to return

        Returns:
            List[AuditLog]: Audit entries
        """
        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == str(resource_id),
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_user_activity(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Get audit history for a user.

        Args:
            user_id: UUID of user
            limit: Maximum entries to return

        Returns:
            List[AuditLog]: Audit entries
        """
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
