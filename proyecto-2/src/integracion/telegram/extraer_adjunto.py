"""Extraccion de metadatos de adjuntos desde mensajes Telegram."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.integracion.telegram.esquemas import TelegramMensaje

TipoAdjuntoEntrada = Literal["imagen", "video", "audio"]


@dataclass(frozen=True)
class AdjuntoEntrada:
    """Descriptor minimo para descargar un archivo de Telegram."""

    file_id: str
    tipo: TipoAdjuntoEntrada
    mime_type: str
    caption: str | None


def _mime_documento_permitido(mime: str | None) -> str | None:
    if not mime:
        return None
    mime_l = mime.strip().lower()
    if mime_l.startswith(("image/", "video/", "audio/")):
        return mime_l
    return None


def extraer_adjunto_telegram(mensaje: TelegramMensaje) -> AdjuntoEntrada | None:
    """
    Prioridad: foto (mayor resolucion) → video → voz → audio → documento multimedia.

    Retorna None si el mensaje no trae adjunto soportado.
    """
    caption = (mensaje.caption or "").strip() or None

    if mensaje.photo:
        mejor = max(mensaje.photo, key=lambda p: p.file_size or 0)
        return AdjuntoEntrada(
            file_id=mejor.file_id,
            tipo="imagen",
            mime_type="image/jpeg",
            caption=caption,
        )

    if mensaje.video:
        mime = (mensaje.video.mime_type or "video/mp4").strip().lower()
        return AdjuntoEntrada(
            file_id=mensaje.video.file_id,
            tipo="video",
            mime_type=mime,
            caption=caption,
        )

    if mensaje.voice:
        mime = (mensaje.voice.mime_type or "audio/ogg").strip().lower()
        return AdjuntoEntrada(
            file_id=mensaje.voice.file_id,
            tipo="audio",
            mime_type=mime,
            caption=caption,
        )

    if mensaje.audio:
        mime = (mensaje.audio.mime_type or "audio/mpeg").strip().lower()
        return AdjuntoEntrada(
            file_id=mensaje.audio.file_id,
            tipo="audio",
            mime_type=mime,
            caption=caption,
        )

    if mensaje.document:
        mime = _mime_documento_permitido(mensaje.document.mime_type)
        if mime is None:
            return None
        tipo: TipoAdjuntoEntrada
        if mime.startswith("image/"):
            tipo = "imagen"
        elif mime.startswith("video/"):
            tipo = "video"
        else:
            tipo = "audio"
        return AdjuntoEntrada(
            file_id=mensaje.document.file_id,
            tipo=tipo,
            mime_type=mime,
            caption=caption,
        )

    return None
