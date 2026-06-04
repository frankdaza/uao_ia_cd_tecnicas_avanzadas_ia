"""Tarea periodica asyncio para recordatorios (UC-MVP-04)."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.configuracion import obtener_configuracion
from src.integracion.recordatorios.estado_job import RecordatoriosJobEstado
from src.integracion.recordatorios.servicio import procesar_recordatorios_pendientes

logger = logging.getLogger(__name__)


async def ejecutar_bucle_recordatorios(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    estado_job: RecordatoriosJobEstado,
    detener: asyncio.Event,
) -> None:
    """Ejecuta el job segun el estado runtime (panel admin) hasta ``detener``."""
    snapshot = await estado_job.leer()
    logger.info(
        "recordatorios_job_iniciado intervalo_seg=%s habilitado=%s",
        snapshot.interval_seg,
        snapshot.habilitado,
    )
    cfg = obtener_configuracion()
    while not detener.is_set():
        try:
            snapshot = await estado_job.leer()
            if snapshot.habilitado:
                resultado = await procesar_recordatorios_pendientes(
                    session_factory,
                    cfg=cfg,
                )
                logger.info(
                    "recordatorios_job_ciclo pendientes=%s enviados=%s intervalo_seg=%s",
                    resultado.pendientes_vencidos,
                    resultado.enviados,
                    snapshot.interval_seg,
                )
        except Exception:
            logger.exception("recordatorios_job_error")
        snapshot = await estado_job.leer()
        intervalo = snapshot.interval_seg
        try:
            await asyncio.wait_for(detener.wait(), timeout=intervalo)
        except TimeoutError:
            continue
    logger.info("recordatorios_job_detenido")
