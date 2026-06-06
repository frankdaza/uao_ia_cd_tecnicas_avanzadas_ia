"""Vincula adjuntos del turno actual a una alerta de triage."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.agentes.contexto import obtener_adjuntos_turno_runtime
from src.persistencia.repositorios.adjuntos_mensaje import RepositorioAdjuntosMensaje

logger = logging.getLogger(__name__)

_SUFIJO_RESUMEN_ADJUNTO = " (incluye adjunto multimedia)"


def enriquecer_resumen_con_adjuntos(resumen: str, hay_adjuntos: bool) -> str:
    if not hay_adjuntos:
        return resumen
    if _SUFIJO_RESUMEN_ADJUNTO.strip(" ()") in resumen:
        return resumen
    texto = resumen.rstrip()
    if len(texto) + len(_SUFIJO_RESUMEN_ADJUNTO) > 1024:
        max_base = 1024 - len(_SUFIJO_RESUMEN_ADJUNTO)
        texto = texto[:max_base].rstrip()
    return f"{texto}{_SUFIJO_RESUMEN_ADJUNTO}"


async def vincular_adjuntos_turno_a_alerta(
    sesion: AsyncSession,
    alerta_id: uuid.UUID,
) -> int:
    """Asocia adjuntos del contexto runtime a la alerta recien creada."""
    adjunto_ids = obtener_adjuntos_turno_runtime()
    if not adjunto_ids:
        return 0
    repo = RepositorioAdjuntosMensaje(sesion)
    await repo.vincular_a_alerta(alerta_id, adjunto_ids)
    logger.info(
        "alerta_adjuntos_vinculados alerta_id=%s cantidad=%s",
        alerta_id,
        len(adjunto_ids),
    )
    return len(adjunto_ids)
