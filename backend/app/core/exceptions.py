"""
Excepciones de dominio.

Estas excepciones se mapean automáticamente a respuestas HTTP estructuradas
en `app.main` (ver `app_error_handler`).
"""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Excepción base para errores de dominio."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class IntegrationError(AppError):
    """Error al hablar con un sistema externo (BIND, Syscom, etc.)."""

    status_code = 502
    code = "integration_error"
