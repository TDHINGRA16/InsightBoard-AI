"""
Logging configuration for the application.
"""

import logging
import sys
from typing import Optional

from app.config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    Configure application-wide logging.

    Args:
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR)
        log_format: Custom log format string

    Returns:
        logging.Logger: Configured root logger
    """
    level = log_level or ("DEBUG" if settings.DEBUG else "INFO")

    format_str = log_format or (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
    )

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger("insightboard")
    logger.info(f"Logging configured at {level} level")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logging.Logger: Named logger instance
    """
    return logging.getLogger(f"insightboard.{name}")
