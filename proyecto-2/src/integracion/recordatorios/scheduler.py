"""Tarea periodica asyncio para recordatorios (UC-MVP-04)."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.configuracion import Configuracion
from src.integracion.recordatorios.servicio import procesar_recordatorios_pendientes

logger = logging.getLogger(__name__)


async def ejecutar_bucle_recordatorios(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    cfg: Configuracion,
    detener: asyncio.Event,
) -> None:
    """Ejecuta el job cada ``cfg.recordatorios_job_interval_seg`` hasta ``detener``."""
    intervalo = max(5, cfg.recordatorios_job_interval_seg)
    logger.info(
        "recordatorios_job_iniciado intervalo_seg=%s habilitado=%s",
        intervalo,
        cfg.recordatorios_job_habilitado,
    )
    while not detener.is_set():
        try:
            if cfg.recordatorios_job_habilitado:
                cantidad = await procesar_recordatorios_pendientes(
                    session_factory,
                    cfg=cfg,
                )
                if cantidad:
                    logger.info("recordatorios_job_ciclo enviados=%s", cantidad)
        except Exception:
            logger.exception("recordatorios_job_error")
        try:
            await asyncio.wait_for(detener.wait(), timeout=intervalo)
        except TimeoutError:
            continue
    logger.info("recordatorios_job_detenido")
