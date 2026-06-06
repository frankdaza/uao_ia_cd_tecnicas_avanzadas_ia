"""Procesamiento de ``Update`` Telegram: emparejamiento y turno /chat."""

from __future__ import annotations

import logging
import re
import uuid

from fastapi import HTTPException
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.esquemas_chat import ChatMetadata, ChatPeticion
from src.api.servicios.chat import _MENSAJE_SIN_VINCULO, _MENSAJE_TIMEOUT, procesar_turno_chat
from src.api.servicios.emparejamiento import EmparejamientoError, emparejar_codigo
from src.configuracion import Configuracion, obtener_configuracion
from src.integracion.telegram.almacenamiento_adjuntos import AdjuntoTelegramInvalidoError
from src.integracion.telegram.cliente import ClienteTelegram
from src.integracion.telegram.errores import TelegramEnvioError
from src.integracion.telegram.esquemas import TelegramMensaje, TelegramUpdate
from src.integracion.telegram.extraer_adjunto import AdjuntoEntrada, extraer_adjunto_telegram
from src.integracion.telegram.persistir_adjunto import persistir_adjunto_telegram
from src.persistencia.repositorios.telegram_updates import RepositorioTelegramUpdates
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram

logger = logging.getLogger(__name__)

_MENSAJE_BIENVENIDA = (
    "Bienvenido al seguimiento postoperatorio TAAM (Fundacion Valle del Lili). "
    "Si recibio un codigo del equipo clinico, envielo asi: /start CODIGO"
)

_MENSAJE_RECHAZO_MULTIMEDIA = (
    "No pudimos procesar ese archivo. Envie una imagen (JPEG o PNG), "
    "un video MP4 o un mensaje de audio dentro del tamano permitido."
)

_MENSAJE_CONFIRMACION_ADJUNTO = {
    "imagen": "Recibimos su imagen. El equipo clinico podra revisarla en su seguimiento.",
    "video": "Recibimos su video. El equipo clinico podra revisarlo en su seguimiento.",
    "audio": "Recibimos su audio. El equipo clinico podra escucharlo en su seguimiento.",
}

_PLACEHOLDER_PACIENTE = {
    "imagen": "[El paciente envio una imagen]",
    "video": "[El paciente envio un video]",
    "audio": "[El paciente envio un audio]",
}

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


def _texto_para_agente(entrada: AdjuntoEntrada) -> str:
    if entrada.caption:
        return entrada.caption
    return _PLACEHOLDER_PACIENTE[entrada.tipo]


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
    if mensaje is None:
        logger.debug("update_sin_mensaje update_id=%s", update.update_id)
        return

    chat_id = mensaje.chat.id
    texto = (mensaje.text or "").strip()
    adjunto = extraer_adjunto_telegram(mensaje)

    async with session_factory() as sesion:
        repo_updates = RepositorioTelegramUpdates(sesion)
        if not await repo_updates.intentar_registrar(update.update_id):
            logger.info("telegram_update_duplicado update_id=%s", update.update_id)
            return
        await sesion.commit()

    try:
        if texto and es_comando_start(texto) and adjunto is None:
            await _manejar_start(
                chat_id=chat_id,
                texto=texto,
                session_factory=session_factory,
                cliente=cliente,
            )
            return

        if adjunto is not None:
            await _manejar_mensaje_multimedia(
                chat_id=chat_id,
                mensaje=mensaje,
                entrada=adjunto,
                update_id=update.update_id,
                session_factory=session_factory,
                checkpointer=checkpointer,
                cliente=cliente,
                cfg=conf,
            )
            return

        if not texto:
            logger.debug("update_sin_texto_ni_adjunto update_id=%s", update.update_id)
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


async def _resolver_caso_vinculado(
    session_factory: async_sessionmaker[AsyncSession],
    chat_id: int,
) -> uuid.UUID | None:
    async with session_factory() as sesion:
        repo = RepositorioVinculosTelegram(sesion)
        vinculo = await repo.obtener_vinculado_por_chat_id(chat_id)
        if vinculo is None:
            return None
        return vinculo.caso_id


async def _manejar_mensaje_multimedia(
    *,
    chat_id: int,
    mensaje: TelegramMensaje,
    entrada: AdjuntoEntrada,
    update_id: int,
    session_factory: async_sessionmaker[AsyncSession],
    checkpointer: BaseCheckpointSaver,
    cliente: ClienteTelegram,
    cfg: Configuracion,
) -> None:
    caso_id = await _resolver_caso_vinculado(session_factory, chat_id)
    if caso_id is None:
        await cliente.enviar_mensaje(chat_id, _MENSAJE_SIN_VINCULO)
        return

    session_id = f"telegram:{chat_id}"
    try:
        adjunto_id = await persistir_adjunto_telegram(
            session_factory=session_factory,
            checkpointer=checkpointer,
            session_id=session_id,
            caso_id=caso_id,
            telegram_message_id=mensaje.message_id,
            entrada=entrada,
            cliente=cliente,
            cfg=cfg,
        )
    except (AdjuntoTelegramInvalidoError, TelegramEnvioError):
        logger.warning(
            "telegram_adjunto_rechazado chat_id=%s message_id=%s",
            chat_id,
            mensaje.message_id,
        )
        await cliente.enviar_mensaje(chat_id, _MENSAJE_RECHAZO_MULTIMEDIA)
        return

    texto_agente = _texto_para_agente(entrada)
    peticion = ChatPeticion(
        session_id=session_id,
        mensaje=texto_agente,
        metadata=ChatMetadata(
            canal="telegram",
            update_id=update_id,
            telegram_message_id=mensaje.message_id,
            caso_id=caso_id,
            adjunto_ids=[adjunto_id],
        ),
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

    confirmacion = _MENSAJE_CONFIRMACION_ADJUNTO[entrada.tipo]
    texto_respuesta = respuesta.respuesta.strip()
    if texto_respuesta:
        texto_final = f"{confirmacion}\n\n{texto_respuesta}"
    else:
        texto_final = confirmacion

    if respuesta.requiere_revision_humana:
        texto_final = (
            f"{texto_final}\n\n"
            "Un miembro del equipo clinico revisara su consulta pronto."
        )

    await cliente.enviar_mensaje(
        chat_id,
        texto_final,
        formatear_markdown=bool(texto_respuesta),
    )


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
    await cliente.enviar_mensaje(
        chat_id,
        texto_respuesta or _MENSAJE_TIMEOUT,
        formatear_markdown=bool(texto_respuesta),
    )
