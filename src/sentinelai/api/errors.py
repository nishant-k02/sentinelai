from __future__ import annotations

from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from sentinelai.platform.errors import SentinelError
from sentinelai.platform.logging import get_logger

logger = get_logger(__name__)


def _body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    err = cast(RequestValidationError, exc)
    detail = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in err.errors())
    logger.warning("request_validation_failed", detail=detail)
    return JSONResponse(status_code=422, content=_body("validation_error", detail))


async def _handle_sentinel_error(request: Request, exc: Exception) -> JSONResponse:
    err = cast(SentinelError, exc)
    logger.warning("request_failed", code=err.code, status=err.http_status, detail=err.message)
    return JSONResponse(status_code=err.http_status, content=_body(err.code, err.message))


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception")
    return JSONResponse(
        status_code=500, content=_body("internal_error", "An unexpected error occurred.")
    )


def register_exception_handlers(app: FastAPI) -> None:
    """One handler per error family. Route code raises domain errors, or
    Pydantic/FastAPI raises a validation error on our behalf — either way,
    the client sees the same {"error": {code, message}} shape."""
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(SentinelError, _handle_sentinel_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
