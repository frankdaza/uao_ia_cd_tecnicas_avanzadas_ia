"""Tool ``consultar_protocolo_rag`` con filtro por procedimiento."""

from __future__ import annotations

import logging

from langchain_core.tools import tool
from qdrant_client.models import FieldCondition, Filter, MatchValue

from src.agentes.contexto import (
    obtener_session_factory_runtime,
    obtener_session_id_runtime,
)
from src.agentes.tools.esquemas import EntradaConsultarProtocoloRag
from src.agentes.tools.resolver_caso import resolver_caso_activo_por_session
from src.configuracion import obtener_configuracion
from src.rag.vector_store import crear_vector_store

logger = logging.getLogger(__name__)

_MENSAJE_SIN_CASO = (
    "No hay un caso vinculado para consultar el protocolo. "
    "Complete el emparejamiento con el codigo del equipo."
)
_MENSAJE_SIN_RESULTADOS = (
    "No encontramos fragmentos del protocolo para esa consulta. "
    "Consulte a su equipo tratante o reporte sus sintomas."
)
_MENSAJE_ERROR = (
    "No pudimos consultar el protocolo en este momento. "
    "El equipo revisara su mensaje."
)


@tool("consultar_protocolo_rag", args_schema=EntradaConsultarProtocoloRag)
async def consultar_protocolo_rag(consulta: str) -> str:
    """
    Recupera fragmentos del PDF de protocolo indexado en Qdrant para el procedimiento del caso.

    Filtra por ``tipo_procedimiento_id`` del paciente vinculado.
    """
    factory = obtener_session_factory_runtime()
    session_id = obtener_session_id_runtime()
    cfg = obtener_configuracion()

    async with factory() as sesion:
        ctx = await resolver_caso_activo_por_session(sesion, session_id)
        if ctx is None:
            return _MENSAJE_SIN_CASO

    try:
        store = crear_vector_store(cfg)
        filtro = Filter(
            must=[
                FieldCondition(
                    key="metadata.tipo_procedimiento_id",
                    match=MatchValue(value=str(ctx.tipo_procedimiento_id)),
                )
            ]
        )
        docs = store.similarity_search(
            consulta,
            k=cfg.agente_rag_k,
            filter=filtro,
        )
    except Exception:
        logger.exception("Fallo consultar_protocolo_rag")
        return _MENSAJE_ERROR

    if not docs:
        return _MENSAJE_SIN_RESULTADOS

    fragmentos = []
    for i, doc in enumerate(docs, start=1):
        fragmentos.append(f"[{i}] {doc.page_content.strip()}")
    return "\n\n".join(fragmentos)
