"""Application-wide exception hierarchy and FastAPI exception handlers.

All domain errors derive from :class:`AppError`, which carries an HTTP
status code, a stable machine-readable ``code`` and an optional ``details``
payload. This guarantees consistent, structured error responses across the
entire API surface.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


# --------------------------------------------------------------------------- #
# Domain exceptions
# --------------------------------------------------------------------------- #
class AppError(Exception):
    """Base class for all expected application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.details = details
        super().__init__(self.message)

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"error": {"code": self.code, "message": self.message}}
        if self.details is not None:
            payload["error"]["details"] = self.details
        return payload


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "The requested resource was not found."


class AuthenticationError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "authentication_error"
    message = "Authentication failed."


class AuthorizationError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "authorization_error"
    message = "You do not have permission to perform this action."


class ValidationAppError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_error"
    message = "The submitted data is invalid."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "The resource already exists or conflicts with current state."


class RateLimitError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"
    message = "Too many requests. Please slow down."


class FileValidationError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "invalid_file"
    message = "The uploaded file is invalid."


class ModelInferenceError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "inference_error"
    message = "Model inference failed."


class PipelineError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "pipeline_error"
    message = "Audio processing pipeline failed."


class StorageError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "storage_error"
    message = "Object storage operation failed."


# --------------------------------------------------------------------------- #
# Exception handlers
# --------------------------------------------------------------------------- #
def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON exception handlers to the FastAPI application."""

    @app.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("app_error", code=exc.code, message=exc.message, details=exc.details)
        else:
            logger.info("app_error", code=exc.code, message=exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed.",
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "http_error", "message": str(exc.detail)}},
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected internal error occurred.",
                }
            },
        )
