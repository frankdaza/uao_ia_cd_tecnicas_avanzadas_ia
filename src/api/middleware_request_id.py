"""Middleware HTTP: correlación por request-id y registro compacto."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("src.api.http")


async def registrar_request_response(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Asigna ``X-Request-ID`` si falta y registra duración de la solicitud."""
    cabecera = request.headers.get("x-request-id")
    rid = cabecera if cabecera and cabecera.strip() else str(uuid.uuid4())
    request.state.request_id = rid

    ruta = request.url.path
    inicio = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - inicio) * 1000
        logger.exception(
            "request_failure id=%s method=%s path=%s elapsed_ms=%.2f",
            rid,
            request.method,
            ruta,
            elapsed_ms,
        )
        raise
    elapsed_ms = (time.perf_counter() - inicio) * 1000
    response.headers["X-Request-ID"] = rid
    logger.info(
        "request id=%s method=%s path=%s status=%s elapsed_ms=%.2f",
        rid,
        request.method,
        ruta,
        getattr(response, "status_code", "?"),
        elapsed_ms,
    )
    return response
