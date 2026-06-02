"""Structured KV de OpenFang via REST (resumen de ingesta)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


def publicar_resumen_ingesta(
    api_base: str,
    agent_id: str,
    resumen: dict[str, Any],
) -> bool:
    """
    PUT ``ingesta:resumen`` en el namespace KV del agente.

    Retorna ``True`` si la API respondio 2xx.
    """
    url = f"{api_base.rstrip('/')}/api/memory/agents/{agent_id}/kv/ingesta:resumen"
    cuerpo = json.dumps(resumen).encode("utf-8")
    peticion = urllib.request.Request(
        url,
        data=cuerpo,
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            return 200 <= respuesta.status < 300
    except urllib.error.URLError as exc:
        logger.warning("No se pudo publicar KV ingesta:resumen: %s", exc)
        return False
