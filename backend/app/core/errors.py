import logging
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "too_many_requests",
}


def error_response(
    status_code: int,
    code: str,
    detail: str,
    errors: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"code": code, "detail": detail}
    if errors:
        body["errors"] = errors
    return JSONResponse(status_code=status_code, content=body, headers=headers)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    http_exc = cast(StarletteHTTPException, exc)
    detail = http_exc.detail if isinstance(http_exc.detail, str) else "Erreur"
    return error_response(
        http_exc.status_code,
        STATUS_CODES.get(http_exc.status_code, "error"),
        detail,
        headers=http_exc.headers,  # conserve WWW-Authenticate pour les 401
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_exc = cast(RequestValidationError, exc)
    errors = []
    for err in validation_exc.errors():
        loc = err["loc"]
        field = ".".join(str(part) for part in loc[1:]) or str(loc[0])
        # On ne renvoie jamais la valeur reçue (« input ») : elle peut être sensible.
        errors.append({"field": field, "message": err["msg"]})
    return error_response(
        422, "validation_error", "Les données envoyées sont invalides.", errors
    )


async def integrity_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Integrity error on %s %s", request.method, request.url.path)
    return error_response(
        409, "conflict", "La requête entre en conflit avec des données existantes."
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return error_response(500, "internal_error", "Une erreur interne est survenue.")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)