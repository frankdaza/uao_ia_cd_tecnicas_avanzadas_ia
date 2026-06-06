"""Pruebas de extraccion de adjuntos desde mensajes Telegram."""

from __future__ import annotations

from src.integracion.telegram.esquemas import (
    TelegramChat,
    TelegramMensaje,
    TelegramPhotoSize,
    TelegramVideo,
    TelegramVoice,
)
from src.integracion.telegram.extraer_adjunto import extraer_adjunto_telegram


def _mensaje_base(**kwargs) -> TelegramMensaje:
    datos = {
        "message_id": 1,
        "chat": TelegramChat(id=99, type="private"),
        **kwargs,
    }
    return TelegramMensaje(**datos)


def test_extraer_foto_con_caption() -> None:
    msg = _mensaje_base(
        photo=[
            TelegramPhotoSize(file_id="small", width=100, height=100, file_size=1000),
            TelegramPhotoSize(file_id="large", width=800, height=600, file_size=50000),
        ],
        caption="Herida abierta",
    )
    entrada = extraer_adjunto_telegram(msg)
    assert entrada is not None
    assert entrada.file_id == "large"
    assert entrada.tipo == "imagen"
    assert entrada.caption == "Herida abierta"


def test_extraer_video_sin_caption() -> None:
    msg = _mensaje_base(
        video=TelegramVideo(file_id="vid-1", mime_type="video/mp4"),
    )
    entrada = extraer_adjunto_telegram(msg)
    assert entrada is not None
    assert entrada.tipo == "video"
    assert entrada.caption is None


def test_extraer_voz() -> None:
    msg = _mensaje_base(
        voice=TelegramVoice(file_id="voice-1", mime_type="audio/ogg"),
    )
    entrada = extraer_adjunto_telegram(msg)
    assert entrada is not None
    assert entrada.tipo == "audio"


def test_sin_adjunto_retorna_none() -> None:
    msg = _mensaje_base(text="solo texto")
    assert extraer_adjunto_telegram(msg) is None
