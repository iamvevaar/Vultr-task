"""
Consistent, structured error responses (a task requirement).

Every error the API returns uses ONE shape (the "envelope"):

    { "error": { "code": "FORBIDDEN", "message": "...", "details": {...} } }

- `code`    : a stable, machine-readable string the frontend can switch on.
- `message` : a human-readable explanation.
- `details` : optional extra data (e.g. per-field validation errors).

We raise `AppError` (via the helper constructors) anywhere in our code, and the
registered handlers convert framework/validation errors into the same shape so
NOTHING escapes with a different structure.
"""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """An error we deliberately raise, carrying everything the envelope needs."""

    def __init__(self, status_code: int, code: str, message: str, details=None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def _envelope(code: str, message: str, details=None) -> dict:
    body = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


# --- Helper constructors: readable at call sites (raise conflict("...")) ------

def bad_request(message="Bad request", details=None):
    return AppError(400, "BAD_REQUEST", message, details)


def unauthorized(message="Authentication required", details=None):
    return AppError(401, "UNAUTHORIZED", message, details)


def forbidden(message="You do not have permission to perform this action", details=None):
    return AppError(403, "FORBIDDEN", message, details)


def not_found(message="Resource not found", details=None):
    return AppError(404, "NOT_FOUND", message, details)


def conflict(message="Resource already exists", details=None):
    return AppError(409, "CONFLICT", message, details)


# --- Wire the handlers onto the app -----------------------------------------

def install_error_handlers(app: FastAPI) -> None:
    """Call once in main.py. Registers handlers so ALL errors use the envelope."""

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(_envelope(exc.code, exc.message, exc.details)),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError):
        # Raised automatically when a request body fails Pydantic validation.
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(
                _envelope("VALIDATION_ERROR", "Request validation failed", exc.errors())
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(request: Request, exc: StarletteHTTPException):
        # Catches things like 404 for unknown routes so they, too, use the envelope.
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(_envelope(f"HTTP_{exc.status_code}", str(exc.detail))),
        )
