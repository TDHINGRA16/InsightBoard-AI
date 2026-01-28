"""
Custom domain exceptions for the application.
"""

from typing import Any, Optional


class InsightBoardException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None,
    ):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class AuthenticationError(InsightBoardException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(InsightBoardException):
    """Raised when user lacks permission for an action."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class NotFoundError(InsightBoardException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
        )


class ValidationError(InsightBoardException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class DuplicateError(InsightBoardException):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            message=f"{resource} with {field}='{value}' already exists",
            code="DUPLICATE_ERROR",
            details={"resource": resource, "field": field, "value": value},
        )


class CyclicDependencyError(InsightBoardException):
    """Raised when a circular dependency is detected in the task graph."""

    def __init__(self, cycle: list):
        super().__init__(
            message="Circular dependency detected in task graph",
            code="CYCLIC_DEPENDENCY",
            details={"cycle": cycle},
        )


class LLMError(InsightBoardException):
    """Raised when LLM processing fails."""

    def __init__(self, message: str = "LLM processing failed"):
        super().__init__(message=message, code="LLM_ERROR")


class JobError(InsightBoardException):
    """Raised when a background job fails."""

    def __init__(self, job_id: str, message: str):
        super().__init__(
            message=message,
            code="JOB_ERROR",
            details={"job_id": job_id},
        )


class RateLimitError(InsightBoardException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED")


class FileProcessingError(InsightBoardException):
    """Raised when file parsing or processing fails."""

    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(
            message=message,
            code="FILE_PROCESSING_ERROR",
            details={"filename": filename} if filename else None,
        )
