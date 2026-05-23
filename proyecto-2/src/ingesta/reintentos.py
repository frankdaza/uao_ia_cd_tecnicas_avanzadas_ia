"""
Reintentos con backoff exponencial para embed/upsert en ingesta TAAM.

Politica alineada con ``proyecto-1/scripts/_utiles_retry.py`` (task-80).
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
    code = getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code
    resp = getattr(exc, "response", None)
    code2 = getattr(resp, "status_code", None) if resp is not None else None
    if isinstance(code2, int):
        return code2
    cause = exc.__cause__
    if isinstance(cause, BaseException) and cause is not exc:
        return _status_http_de(cause)
    return None


def excepcion_es_reintentable(exc: BaseException) -> bool:
    """HTTP 400, 401 y 403 no se reintentan."""
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
    etiqueta: str,
) -> T:
    """Ejecuta ``fn`` con reintentos y backoff exponencial (base 2)."""
    intentos_max = max(1, intentos)

    def _antes_dormir(retry_state: RetryCallState) -> None:
        exc = retry_state.outcome.exception()
        na = retry_state.next_action
        espera = float(getattr(na, "sleep", 0.0) or 0.0) if na is not None else 0.0
        log.warning(
            "Reintento ingesta TAAM intento=%s/%s operacion=%s etiqueta=%s tipo=%s espera_s=%.2f",
            retry_state.attempt_number,
            intentos_max,
            operacion,
            etiqueta,
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
    return r(fn)
