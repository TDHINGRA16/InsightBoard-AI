"""
Global exception handlers for consistent error responses.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CyclicDependencyError,
    DuplicateError,
    FileProcessingError,
    InsightBoardException,
    JobError,
    LLMError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers for the application.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        """Handle authentication failures."""
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
            },
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        """Handle authorization failures."""
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
            },
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(
        request: Request, exc: NotFoundError
    ) -> JSONResponse:
        """Handle resource not found errors."""
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle validation errors."""
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )

    @app.exception_handler(DuplicateError)
    async def duplicate_error_handler(
        request: Request, exc: DuplicateError
    ) -> JSONResponse:
        """Handle duplicate resource errors."""
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )

    @app.exception_handler(CyclicDependencyError)
    async def cyclic_dependency_error_handler(
        request: Request, exc: CyclicDependencyError
    ) -> JSONResponse:
        """Handle circular dependency errors."""
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )

    @app.exception_handler(LLMError)
    async def llm_error_handler(request: Request, exc: LLMError) -> JSONResponse:
        """Handle LLM processing errors."""
        logger.error(f"LLM error: {exc.message}")
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
            },
        )

    @app.exception_handler(JobError)
    async def job_error_handler(request: Request, exc: JobError) -> JSONResponse:
        """Handle background job errors."""
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(
        request: Request, exc: RateLimitError
    ) -> JSONResponse:
        """Handle rate limiting errors."""
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
            },
        )

    @app.exception_handler(FileProcessingError)
    async def file_processing_error_handler(
        request: Request, exc: FileProcessingError
    ) -> JSONResponse:
        """Handle file processing errors."""
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
                "details": exc.details,
            },
        )

    @app.exception_handler(InsightBoardException)
    async def insightboard_error_handler(
        request: Request, exc: InsightBoardException
    ) -> JSONResponse:
        """Handle generic application errors."""
        logger.error(f"Application error: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": exc.message,
                "code": exc.code,
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected errors."""
        logger.exception(f"Unexpected error: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR",
            },
        )
