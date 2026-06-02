"""Disparo de ingesta PDF en segundo plano desde la API admin."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.configuracion import obtener_configuracion
from src.ingesta.protocolo_ingesta import ejecutar_ingesta_en_sesion_nueva

logger = logging.getLogger(__name__)


async def ingesta_protocolo_background(
    session_factory: async_sessionmaker,
    tipo_id: uuid.UUID,
    *,
    forzar: bool = False,
) -> None:
    """
    Tarea en background tras POST/PATCH con PDF.

    Usa una sesion nueva para no compartir estado con la peticion HTTP.
    """
    cfg = obtener_configuracion()
    try:
        res = await ejecutar_ingesta_en_sesion_nueva(
            session_factory,
            tipo_id,
            cfg=cfg,
            forzar=forzar,
        )
        if res.noop:
            logger.info("Ingesta background omitida (no-op) tipo_id=%s", tipo_id)
        else:
            logger.info(
                "Ingesta background tipo_id=%s chunks=%s estado_msg=%s",
                tipo_id,
                res.chunks,
                res.mensaje,
            )
    except Exception:
        logger.exception("Ingesta background fallo tipo_id=%s", tipo_id)
