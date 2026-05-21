"""
Observabilidad LangSmith / LangChain: sincronizar variables de proceso para tracing.

LangChain lee ``LANGCHAIN_*`` desde el entorno del proceso. ``pydantic-settings`` carga
``.env`` en el modelo ``Configuracion`` pero no reexporta automaticamente esos valores
a ``os.environ``; este modulo aplica la politica de activacion en un unico lugar (DRY).
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.api.configuracion import Configuracion

logger = logging.getLogger(__name__)


def aplicar_tracing_langchain_desde_config(cfg: Configuracion) -> None:
    """
    Si las trazas estan activas y hay clave API, escribe variables que el SDK de LangChain
    usa para exportar runs a LangSmith.

    Si las trazas estan desactivadas en la configuracion cargada, no modifica el entorno
    (permite que variables ya exportadas en el shell sigan vigentes).
    """
    if not cfg.trazas_langchain_activas:
        # INFO: en Docker suele faltar el `.env` montado; sin variables en compose el nivel DEBUG no se ve en Uvicorn.
        logger.info(
            "langchain.tracing: export desactivado (LANGCHAIN_TRACING_V2 o LANGSMITH_TRACING "
            "no estan en true en la configuracion efectiva del proceso)."
        )
        return

    clave = (cfg.clave_api_trazas_langchain or "").strip()
    if not clave:
        logger.warning(
            "langchain.tracing: trazas activadas pero falta LANGCHAIN_API_KEY o "
            "LANGSMITH_API_KEY; no se habilita el export de trazas."
        )
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = clave

    proyecto = (cfg.proyecto_trazas_langchain or "").strip()
    if proyecto:
        os.environ["LANGCHAIN_PROJECT"] = proyecto

    url_ep = (cfg.url_endpoint_trazas_langchain or "").strip()
    if url_ep:
        os.environ["LANGCHAIN_ENDPOINT"] = url_ep

    logger.info(
        "langchain.tracing: export habilitado (proyecto_configurado=%s endpoint_configurado=%s)",
        bool(proyecto),
        bool(url_ep),
    )
