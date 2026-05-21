"""
Reintentos con backoff exponencial para llamadas transitorias en ingesta Qdrant.

Usado desde ``indexar_corpus_qdrant`` para ``get_text_embedding_batch`` y
``cliente.upsert``. Los HTTP 400, 401 y 403 no se reintentan.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TypeVar

from tenacity import (
    Retrying,
    RetryCallState,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

T = TypeVar("T")


def _status_http_de(exc: BaseException) -> int | None:
    """Obtiene un codigo HTTP si la excepcion (o su causa) lo expone."""
    code = getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code
    resp = getattr(exc, "response", None)
    code2 = getattr(resp, "status_code", None) if resp is not None else None
    if isinstance(code2, int):
        return code2
    cause = exc.__cause__
    if isinstance(cause, BaseException) and cause is not exc:
        nested = _status_http_de(cause)
        if nested is not None:
            return nested
    return None


def excepcion_es_reintentable(exc: BaseException) -> bool:
    """
    Retorna ``True`` si la politica de reintento aplica (error transitorio).

    Los codigos 400, 401 y 403 se consideran fallos definitivos del cliente o
    credenciales y no deben reintentarse.
    """
    code = _status_http_de(exc)
    if code in (400, 401, 403):
        return False
    return True


def ejecutar_con_reintentos(
    fn: Callable[[], T],
    *,
    intentos: int,
    espera_max_seg: float,
    log: logging.Logger,
    operacion: str,
    etiqueta_lote: str,
) -> T:
    """
    Ejecuta ``fn`` con reintentos, backoff exponencial (base 2) y tope de espera.

    Registra cada espera previa a un reintento. Si la excepcion no es
    reintentable, registra un error claro y relanza.
    """
    intentos_max = max(1, intentos)

    def _antes_dormir(retry_state: RetryCallState) -> None:
        exc = retry_state.outcome.exception()
        na = retry_state.next_action
        espera = float(getattr(na, "sleep", 0.0) or 0.0) if na is not None else 0.0
        log.warning(
            "Reintento ingesta intento=%s/%s operacion=%s lote=%s tipo_exc=%s espera_s=%.2f",
            retry_state.attempt_number,
            intentos_max,
            operacion,
            etiqueta_lote,
            type(exc).__name__,
            espera,
        )

    r = Retrying(
        stop=stop_after_attempt(intentos_max),
        wait=wait_exponential(multiplier=1, min=1, max=espera_max_seg),
        retry=retry_if_exception(excepcion_es_reintentable),
        reraise=True,
        before_sleep=_antes_dormir,
    )

    try:
        return r(fn)
    except BaseException as exc:
        if not excepcion_es_reintentable(exc):
            log.error(
                "Fallo no transitorio (no se reintenta): operacion=%s lote=%s tipo=%s "
                "http_status=%s detalle=%s",
                operacion,
                etiqueta_lote,
                type(exc).__name__,
                _status_http_de(exc),
                exc,
            )
        raise
