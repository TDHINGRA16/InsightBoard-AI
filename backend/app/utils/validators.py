"""
Validation utilities for input validation.
"""

import os
import re
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import ValidationError


def validate_uuid(value: str, field_name: str = "id") -> UUID:
    """
    Validate a UUID string.

    Args:
        value: String to validate
        field_name: Name of field for error message

    Returns:
        UUID: Parsed UUID

    Raises:
        ValidationError: If not a valid UUID
    """
    try:
        return UUID(value)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid {field_name}: must be a valid UUID")


def validate_file_extension(
    filename: str,
    allowed_extensions: List[str],
) -> str:
    """
    Validate file extension.

    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (with dot)

    Returns:
        str: File extension

    Raises:
        ValidationError: If extension not allowed
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in allowed_extensions:
        raise ValidationError(
            f"Invalid file type: {ext}. Allowed: {', '.join(allowed_extensions)}"
        )

    return ext


def validate_file_size(
    size_bytes: int,
    max_size_mb: int,
) -> None:
    """
    Validate file size.

    Args:
        size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in MB

    Raises:
        ValidationError: If file too large
    """
    max_bytes = max_size_mb * 1024 * 1024

    if size_bytes > max_bytes:
        raise ValidationError(
            f"File too large: {size_bytes / 1024 / 1024:.1f}MB. "
            f"Maximum: {max_size_mb}MB"
        )


def validate_url(url: str) -> str:
    """
    Validate a URL.

    Args:
        url: URL to validate

    Returns:
        str: Validated URL

    Raises:
        ValidationError: If not a valid URL
    """
    # Basic URL pattern
    pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"  # domain
        r"[A-Z]{2,6}\.?|"  # TLD
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not pattern.match(url):
        raise ValidationError(f"Invalid URL: {url}")

    return url


def validate_email(email: str) -> str:
    """
    Validate an email address.

    Args:
        email: Email to validate

    Returns:
        str: Validated email

    Raises:
        ValidationError: If not a valid email
    """
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    if not pattern.match(email):
        raise ValidationError(f"Invalid email: {email}")

    return email.lower()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    # Remove path separators and null bytes
    filename = filename.replace("/", "_")
    filename = filename.replace("\\", "_")
    filename = filename.replace("\0", "")

    # Remove leading/trailing whitespace and dots
    filename = filename.strip(" .")

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext

    return filename or "unnamed"


def validate_positive_int(
    value: int,
    field_name: str,
    max_value: Optional[int] = None,
) -> int:
    """
    Validate a positive integer.

    Args:
        value: Value to validate
        field_name: Field name for error message
        max_value: Optional maximum value

    Returns:
        int: Validated value

    Raises:
        ValidationError: If validation fails
    """
    if value < 0:
        raise ValidationError(f"{field_name} must be non-negative")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}")

    return value
