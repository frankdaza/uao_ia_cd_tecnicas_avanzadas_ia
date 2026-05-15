"""Utilidades para parsear respuestas SSE del agente en pruebas E2E."""

from __future__ import annotations

import json
from typing import Any


def parsear_eventos_sse(cuerpo: bytes) -> list[tuple[str, dict[str, Any]]]:
    """Parsea cuerpo ``text/event-stream`` en lista ``(nombre_evento, payload_json)``."""
    salida: list[tuple[str, dict[str, Any]]] = []
    buffer = cuerpo.decode("utf-8", errors="replace")
    evento_actual: str | None = None
    for linea in buffer.splitlines():
        if linea.startswith("event:"):
            evento_actual = linea.split(":", 1)[1].strip()
        elif linea.startswith("data:") and evento_actual:
            raw = linea[5:].strip()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                evento_actual = None
                continue
            salida.append((evento_actual, payload))
            evento_actual = None
    return salida
