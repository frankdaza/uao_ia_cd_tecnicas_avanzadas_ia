"""Lectura de historial episodico JSONL bajo OPENFANG_HOME."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from pathlib import Path

logger = logging.getLogger(__name__)

_NOMBRES_AUDITORIA = ("hand_recordatorio", "hand_evidencia")


def extraer_session_id(registro: dict) -> str | None:
    """Obtiene session_id de un evento JSONL (variantes de clave OpenFang)."""
    for clave in ("session_id", "sessionId", "session"):
        valor = registro.get(clave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return None


def iterar_registros_jsonl(
    raiz: Path,
    *,
    incluir_audit: bool = False,
) -> Iterator[tuple[Path, dict]]:
    """
    Recorre todos los ``*.jsonl`` bajo ``raiz``.

    Por defecto omite archivos de auditoria Hand (``hand_recordatorio``, ``hand_evidencia``).
    """
    if not raiz.is_dir():
        return
    for ruta in sorted(raiz.rglob("*.jsonl")):
        if not incluir_audit and any(nombre in ruta.name for nombre in _NOMBRES_AUDITORIA):
            continue
        try:
            contenido = ruta.read_text(encoding="utf-8")
        except OSError:
            logger.warning("No se pudo leer JSONL: %s", ruta)
            continue
        for linea in contenido.splitlines():
            linea = linea.strip()
            if not linea:
                continue
            try:
                registro = json.loads(linea)
            except json.JSONDecodeError:
                continue
            if isinstance(registro, dict):
                yield ruta, registro


def filtrar_por_session_id(
    raiz: Path,
    session_id: str,
    *,
    incluir_audit: bool = False,
) -> list[dict]:
    """Devuelve registros cuyo ``session_id`` coincide (comparacion exacta)."""
    objetivo = session_id.strip()
    if not objetivo:
        return []
    return [
        registro
        for _ruta, registro in iterar_registros_jsonl(raiz, incluir_audit=incluir_audit)
        if extraer_session_id(registro) == objetivo
    ]
