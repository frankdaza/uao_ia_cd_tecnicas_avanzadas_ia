"""Procesamiento de ``Update`` Telegram: emparejamiento y turno /chat."""

from __future__ import annotations

import logging
import re

from fastapi import HTTPException
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.esquemas_chat import ChatMetadata, ChatPeticion
from src.api.servicios.chat import _MENSAJE_SIN_VINCULO, _MENSAJE_TIMEOUT, procesar_turno_chat
from src.api.servicios.emparejamiento import EmparejamientoError, emparejar_codigo
from src.configuracion import Configuracion, obtener_configuracion
from src.integracion.telegram.cliente import ClienteTelegram
from src.integracion.telegram.esquemas import TelegramUpdate
from src.persistencia.repositorios.telegram_updates import RepositorioTelegramUpdates

logger = logging.getLogger(__name__)

_MENSAJE_BIENVENIDA = (
    "Bienvenido al seguimiento postoperatorio TAAM (Fundacion Valle del Lili). "
    "Si recibio un codigo del equipo clinico, envielo asi: /start CODIGO"
)

_PATRON_START = re.compile(r"^/start(?:@\w+)?(?:\s+(.+))?$", re.IGNORECASE)


def extraer_codigo_start(texto: str) -> str | None:
    """Extrae el codigo de ``/start CODIGO`` o ``/start@bot CODIGO``."""
    m = _PATRON_START.match(texto.strip())
    if not m:
        return None
    grupo = m.group(1)
    if not grupo:
        return None
    return grupo.strip().upper()


def es_comando_start(texto: str) -> bool:
    return texto.strip().lower().startswith("/start")


async def procesar_update_telegram(
    update: TelegramUpdate,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    checkpointer: BaseCheckpointSaver,
    cliente_telegram: ClienteTelegram | None = None,
    cfg: Configuracion | None = None,
) -> None:
    """
    Maneja un update de Telegram: idempotencia, /start, turno de chat y envio.

    No propaga HTTPException hacia el router; mapea errores a mensajes al paciente.
    """
    conf = cfg or obtener_configuracion()
    cliente = cliente_telegram or ClienteTelegram(conf)

    mensaje = update.message
    if mensaje is None or mensaje.text is None:
        logger.debug("update_sin_mensaje_texto update_id=%s", update.update_id)
        return

    chat_id = mensaje.chat.id
    texto = mensaje.text.strip()
    if not texto:
        return

    async with session_factory() as sesion:
        repo_updates = RepositorioTelegramUpdates(sesion)
        if not await repo_updates.intentar_registrar(update.update_id):
            logger.info("telegram_update_duplicado update_id=%s", update.update_id)
            return
        await sesion.commit()

    try:
        if es_comando_start(texto):
            await _manejar_start(
                chat_id=chat_id,
                texto=texto,
                session_factory=session_factory,
                cliente=cliente,
            )
            return

        await _manejar_mensaje_chat(
            chat_id=chat_id,
            texto=texto,
            update_id=update.update_id,
            session_factory=session_factory,
            checkpointer=checkpointer,
            cliente=cliente,
            cfg=conf,
        )
    except Exception:
        logger.exception(
            "telegram_update_error update_id=%s chat_id=%s",
            update.update_id,
            chat_id,
        )
        await cliente.enviar_mensaje(chat_id, _MENSAJE_TIMEOUT)


async def _manejar_start(
    *,
    chat_id: int,
    texto: str,
    session_factory: async_sessionmaker[AsyncSession],
    cliente: ClienteTelegram,
) -> None:
    codigo = extraer_codigo_start(texto)
    if not codigo:
        await cliente.enviar_mensaje(chat_id, _MENSAJE_BIENVENIDA)
        return

    async with session_factory() as sesion:
        try:
            resultado = await emparejar_codigo(
                sesion,
                codigo=codigo,
                telegram_chat_id=chat_id,
            )
            await sesion.commit()
        except EmparejamientoError as exc:
            await sesion.rollback()
            await cliente.enviar_mensaje(chat_id, exc.mensaje_telegram)
            return

    await cliente.enviar_mensaje(chat_id, resultado.mensaje_confirmacion)


async def _manejar_mensaje_chat(
    *,
    chat_id: int,
    texto: str,
    update_id: int,
    session_factory: async_sessionmaker[AsyncSession],
    checkpointer: BaseCheckpointSaver,
    cliente: ClienteTelegram,
    cfg: Configuracion,
) -> None:
    session_id = f"telegram:{chat_id}"
    peticion = ChatPeticion(
        session_id=session_id,
        mensaje=texto,
        metadata=ChatMetadata(canal="telegram", update_id=update_id),
    )

    try:
        respuesta = await procesar_turno_chat(
            peticion=peticion,
            session_factory=session_factory,
            checkpointer=checkpointer,
            cfg=cfg,
        )
    except HTTPException as exc:
        if exc.status_code == 403:
            detalle = exc.detail if isinstance(exc.detail, str) else _MENSAJE_SIN_VINCULO
            await cliente.enviar_mensaje(chat_id, detalle)
            return
        if exc.status_code == 503:
            detalle = exc.detail if isinstance(exc.detail, str) else _MENSAJE_TIMEOUT
            await cliente.enviar_mensaje(chat_id, detalle)
            return
        raise

    texto_respuesta = respuesta.respuesta.strip()
    if respuesta.requiere_revision_humana and texto_respuesta:
        texto_respuesta = (
            f"{texto_respuesta}\n\n"
            "Un miembro del equipo clinico revisara su consulta pronto."
        )
    await cliente.enviar_mensaje(chat_id, texto_respuesta or _MENSAJE_TIMEOUT)
