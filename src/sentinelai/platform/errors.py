from __future__ import annotations


class SentinelError(Exception):
    """Base class for all application errors.

    Carries a stable machine-readable ``code`` and an HTTP status. The API
    layer (phase 0.4) installs one exception handler that turns any subclass
    into a consistent JSON error body, so handlers never format errors by hand.
    """

    code: str = "internal_error"
    http_status: int = 500

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class NotFoundError(SentinelError):
    code = "not_found"
    http_status = 404


class ValidationError(SentinelError):
    code = "validation_error"
    http_status = 422


class ConflictError(SentinelError):
    code = "conflict"
    http_status = 409


class AuthenticationError(SentinelError):
    code = "unauthenticated"
    http_status = 401


class AuthorizationError(SentinelError):
    code = "forbidden"
    http_status = 403


class ExternalServiceError(SentinelError):
    """A downstream dependency (LLM, vector DB, message broker) failed."""

    code = "external_service_error"
    http_status = 502
