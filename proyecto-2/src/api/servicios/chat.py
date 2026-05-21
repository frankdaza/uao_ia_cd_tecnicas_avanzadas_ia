"""Logica de ``POST /chat``: validacion de vinculo e invocacion del agente."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import HTTPException, status as estado_http
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.agentes.contexto import parsear_session_telegram
from src.agentes.servicio import (
    extraer_fuentes_respuesta,
    extraer_severidad_triage,
    extraer_texto_respuesta,
    invocar_agente,
    requiere_revision_humana,
)
from src.api.esquemas_chat import ChatPeticion, ChatRespuesta, FuenteChat
from src.configuracion import Configuracion, obtener_configuracion
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram

logger = logging.getLogger(__name__)

_MENSAJE_SIN_VINCULO = (
    "Su cuenta de Telegram no esta vinculada a un caso activo. "
    "Use el codigo de emparejamiento que le entrego el equipo clinico "
    "(comando /start CODIGO en el bot)."
)
_MENSAJE_TIMEOUT = (
    "El asistente no respondio a tiempo. Por favor intente de nuevo en unos minutos. "
    "Si tiene una emergencia, acuda a urgencias de inmediato."
)
_MENSAJE_SESSION_INVALIDA = (
    "El identificador de sesion no es valido. Debe usar el formato telegram:{chat_id}."
)


async def sesion_tiene_vinculo_activo(
    sesion: AsyncSession,
    session_id: str,
) -> bool:
    """True si existe vinculo Telegram con ``vinculado_at`` para el chat_id."""
    sesion_tg = parsear_session_telegram(session_id)
    if sesion_tg is None:
        return False
    repo = RepositorioVinculosTelegram(sesion)
    vinculo = await repo.obtener_vinculado_por_chat_id(sesion_tg.chat_id)
    return vinculo is not None


async def procesar_turno_chat(
    *,
    peticion: ChatPeticion,
    session_factory: async_sessionmaker[AsyncSession],
    checkpointer: BaseCheckpointSaver,
    cfg: Configuracion | None = None,
) -> ChatRespuesta:
    """
    Valida vinculo, invoca el agente con timeout y mapea la respuesta JSON.

    Raises:
        HTTPException: 403 sin vinculo, 503 por timeout u otros fallos controlados.
    """
    conf = cfg or obtener_configuracion()
    sesion_tg = parsear_session_telegram(peticion.session_id)
    if sesion_tg is None:
        raise HTTPException(
            status_code=estado_http.HTTP_403_FORBIDDEN,
            detail=_MENSAJE_SESSION_INVALIDA,
        )

    async with session_factory() as sesion:
        if not await sesion_tiene_vinculo_activo(sesion, peticion.session_id):
            raise HTTPException(
                status_code=estado_http.HTTP_403_FORBIDDEN,
                detail=_MENSAJE_SIN_VINCULO,
            )

    update_id = peticion.metadata.update_id if peticion.metadata else None
    logger.info(
        "chat_turno_inicio session_id=%s update_id=%s canal=%s",
        peticion.session_id,
        update_id,
        peticion.metadata.canal if peticion.metadata else None,
    )

    try:
        estado: dict[str, Any] = await asyncio.wait_for(
            invocar_agente(
                session_factory=session_factory,
                checkpointer=checkpointer,
                session_id=peticion.session_id,
                mensaje=peticion.mensaje,
            ),
            timeout=conf.chat_timeout_seg,
        )
    except TimeoutError as exc:
        logger.warning(
            "chat_turno_timeout session_id=%s update_id=%s",
            peticion.session_id,
            update_id,
        )
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_MENSAJE_TIMEOUT,
        ) from exc
    except Exception:
        logger.exception(
            "chat_turno_error session_id=%s update_id=%s",
            peticion.session_id,
            update_id,
        )
        raise HTTPException(
            status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_MENSAJE_TIMEOUT,
        )

    fuentes_raw = extraer_fuentes_respuesta(estado, max_fuentes=conf.agente_rag_k)
    return ChatRespuesta(
        respuesta=extraer_texto_respuesta(estado),
        severidad_triage=extraer_severidad_triage(estado),
        requiere_revision_humana=requiere_revision_humana(estado),
        fuentes=[FuenteChat(**f) for f in fuentes_raw],
        error=None,
    )
