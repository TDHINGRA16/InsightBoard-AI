"""
Formatting utilities for data normalization.
"""

from datetime import datetime, timezone
from typing import Optional, Union
import re


def normalize_date(
    date_input: Union[str, datetime, None],
) -> Optional[datetime]:
    """
    Normalize various date formats to datetime.

    Args:
        date_input: Date string or datetime

    Returns:
        Optional[datetime]: Normalized datetime with timezone
    """
    if date_input is None:
        return None

    if isinstance(date_input, datetime):
        # Ensure timezone aware
        if date_input.tzinfo is None:
            return date_input.replace(tzinfo=timezone.utc)
        return date_input

    if not isinstance(date_input, str):
        return None

    # Try various formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_input, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    # Try ISO format with timezone
    try:
        return datetime.fromisoformat(date_input.replace("Z", "+00:00"))
    except ValueError:
        pass

    return None


def format_duration(hours: float) -> str:
    """
    Format duration in hours to human readable string.

    Args:
        hours: Duration in hours

    Returns:
        str: Human readable duration
    """
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes}m"
    elif hours < 24:
        if hours == int(hours):
            return f"{int(hours)}h"
        return f"{hours:.1f}h"
    else:
        days = hours / 24
        if days == int(days):
            return f"{int(days)}d"
        return f"{days:.1f}d"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size to human readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Human readable size
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            if unit == "B":
                return f"{size_bytes} {unit}"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.1f} TB"


def slugify(text: str) -> str:
    """
    Convert text to URL-safe slug.

    Args:
        text: Text to slugify

    Returns:
        str: URL-safe slug
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)

    # Remove non-alphanumeric characters (except hyphens)
    slug = re.sub(r"[^a-z0-9-]", "", slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Strip leading/trailing hyphens
    slug = slug.strip("-")

    return slug[:100]  # Limit length


def truncate(
    text: str,
    max_length: int,
    suffix: str = "...",
) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from text.

    Args:
        text: Text to clean

    Returns:
        str: Cleaned text
    """
    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)

    # Replace multiple newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def extract_numbers(text: str) -> list:
    """
    Extract all numbers from text.

    Args:
        text: Text to extract from

    Returns:
        list: List of numbers found
    """
    pattern = r"-?\d+\.?\d*"
    matches = re.findall(pattern, text)

    numbers = []
    for match in matches:
        try:
            if "." in match:
                numbers.append(float(match))
            else:
                numbers.append(int(match))
        except ValueError:
            pass

    return numbers
