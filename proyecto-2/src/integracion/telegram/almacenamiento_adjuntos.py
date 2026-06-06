"""Validacion y almacenamiento en disco de adjuntos Telegram."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.configuracion import Configuracion
from src.rutas_workspace import resolver_ruta_workspace

TipoAdjunto = Literal["imagen", "video", "audio"]

_MIME_A_EXTENSION: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
}

_MIME_PERMITIDOS: frozenset[str] = frozenset(_MIME_A_EXTENSION.keys())


class AdjuntoTelegramInvalidoError(ValueError):
    """Adjunto rechazado por tipo, tamano o contenido vacio."""


@dataclass(frozen=True)
class AdjuntoGuardado:
    """Resultado de persistir bytes en disco."""

    ruta_relativa: str
    tamano_bytes: int
    mime_type: str
    tipo: TipoAdjunto


def ruta_relativa_adjunto(caso_id: uuid.UUID, adjunto_id: uuid.UUID, extension: str) -> str:
    ext = extension if extension.startswith(".") else f".{extension}"
    return f"data/taam/adjuntos/{caso_id}/{adjunto_id}{ext}"


def ruta_absoluta_adjunto(ruta_relativa: str) -> Path:
    return resolver_ruta_workspace(ruta_relativa)


def inferir_tipo_desde_mime(mime_type: str) -> TipoAdjunto:
    mime = mime_type.strip().lower()
    if mime.startswith("image/"):
        return "imagen"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"
    raise AdjuntoTelegramInvalidoError(f"Tipo MIME no soportado: {mime_type}")


def validar_mime_permitido(mime_type: str) -> str:
    mime = mime_type.strip().lower()
    if mime not in _MIME_PERMITIDOS:
        raise AdjuntoTelegramInvalidoError(
            "Formato no soportado. Envie imagen (JPEG/PNG), video MP4 o audio."
        )
    return mime


def extension_para_mime(mime_type: str) -> str:
    ext = _MIME_A_EXTENSION.get(mime_type.strip().lower())
    if ext is None:
        raise AdjuntoTelegramInvalidoError(f"Sin extension conocida para MIME {mime_type}")
    return ext


def validar_tamano(contenido: bytes, cfg: Configuracion) -> None:
    if not contenido:
        raise AdjuntoTelegramInvalidoError("El archivo adjunto esta vacio.")
    max_bytes = cfg.taam_adjunto_max_mb * 1024 * 1024
    if len(contenido) > max_bytes:
        raise AdjuntoTelegramInvalidoError(
            f"El archivo supera el tamano maximo permitido ({cfg.taam_adjunto_max_mb} MB)."
        )


def guardar_adjunto_en_disco(
    *,
    caso_id: uuid.UUID,
    contenido: bytes,
    mime_type: str,
    cfg: Configuracion,
    adjunto_id: uuid.UUID | None = None,
) -> AdjuntoGuardado:
    """Escribe bytes validados bajo ``data/taam/adjuntos/{caso_id}/``."""
    validar_tamano(contenido, cfg)
    mime = validar_mime_permitido(mime_type)
    tipo = inferir_tipo_desde_mime(mime)
    aid = adjunto_id or uuid.uuid4()
    extension = extension_para_mime(mime)
    rel = ruta_relativa_adjunto(caso_id, aid, extension)
    destino = ruta_absoluta_adjunto(rel)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    return AdjuntoGuardado(
        ruta_relativa=rel,
        tamano_bytes=len(contenido),
        mime_type=mime,
        tipo=tipo,
    )


def resolver_ruta_segura_adjunto(ruta_relativa: str) -> Path:
    """Evita servir archivos fuera del directorio de adjuntos TAAM."""
    base = resolver_ruta_workspace("data/taam/adjuntos").resolve()
    destino = resolver_ruta_workspace(ruta_relativa).resolve()
    if not str(destino).startswith(str(base)):
        raise AdjuntoTelegramInvalidoError("Ruta de adjunto fuera del directorio permitido.")
    if not destino.is_file():
        raise FileNotFoundError(destino)
    return destino
