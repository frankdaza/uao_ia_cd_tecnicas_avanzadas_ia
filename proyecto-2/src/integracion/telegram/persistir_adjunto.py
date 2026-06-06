"""Persistencia de adjuntos Telegram en disco y OLTP."""

from __future__ import annotations

import logging
import uuid

from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.servicios.historial_conversacion import contar_mensajes_hilo, listar_mensajes_hilo
from src.configuracion import Configuracion
from src.integracion.telegram.almacenamiento_adjuntos import (
    AdjuntoTelegramInvalidoError,
    guardar_adjunto_en_disco,
)
from src.integracion.telegram.cliente import ClienteTelegram
from src.integracion.telegram.errores import TelegramEnvioError
from src.integracion.telegram.extraer_adjunto import AdjuntoEntrada
from src.persistencia.repositorios.adjuntos_mensaje import RepositorioAdjuntosMensaje

logger = logging.getLogger(__name__)


async def indice_siguiente_mensaje_hilo(
    checkpointer: BaseCheckpointSaver,
    session_id: str,
) -> int:
    """Indice del proximo mensaje humano/assistant en la vista de conversacion."""
    mensajes = await listar_mensajes_hilo(checkpointer, session_id)
    return contar_mensajes_hilo(mensajes)


async def persistir_adjunto_telegram(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    checkpointer: BaseCheckpointSaver,
    session_id: str,
    caso_id: uuid.UUID,
    telegram_message_id: int,
    entrada: AdjuntoEntrada,
    cliente: ClienteTelegram,
    cfg: Configuracion,
) -> uuid.UUID:
    """
    Descarga el archivo de Telegram, lo guarda en disco y crea fila OLTP.

    Retorna el UUID del adjunto persistido.
    """
    async with session_factory() as sesion:
        repo = RepositorioAdjuntosMensaje(sesion)
        existente = await repo.existe_por_file_id(caso_id, entrada.file_id)
        if existente is not None:
            await sesion.commit()
            return existente.id

        indice_hilo = await indice_siguiente_mensaje_hilo(checkpointer, session_id)
        adjunto_id = uuid.uuid4()

        try:
            contenido = await cliente.descargar_por_file_id(entrada.file_id)
        except TelegramEnvioError as exc:
            logger.error(
                "telegram_descarga_fallo caso_id=%s file_id=%s status=%s",
                caso_id,
                entrada.file_id,
                exc.status_code,
            )
            raise

        try:
            guardado = guardar_adjunto_en_disco(
                caso_id=caso_id,
                contenido=contenido,
                mime_type=entrada.mime_type,
                cfg=cfg,
                adjunto_id=adjunto_id,
            )
        except AdjuntoTelegramInvalidoError:
            raise

        rel = guardado.ruta_relativa

        fila = await repo.crear(
            caso_id=caso_id,
            telegram_message_id=telegram_message_id,
            telegram_file_id=entrada.file_id,
            tipo=guardado.tipo,
            mime_type=guardado.mime_type,
            tamano_bytes=guardado.tamano_bytes,
            ruta_relativa=rel,
            indice_hilo=indice_hilo,
            caption=entrada.caption,
            adjunto_id=adjunto_id,
        )
        await sesion.commit()
        logger.info(
            "adjunto_telegram_guardado caso_id=%s adjunto_id=%s tipo=%s bytes=%s",
            caso_id,
            fila.id,
            guardado.tipo,
            guardado.tamano_bytes,
        )
        return fila.id
