"""Validacion y almacenamiento de PDFs de protocolo TAAM en el workspace."""

from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from fastapi import status as estado_http

from src.configuracion import Configuracion
from src.rutas_workspace import resolver_ruta_workspace

_PREFIJO_MAGIC_PDF = b"%PDF"
_NOMBRE_ARCHIVO_PERMITIDO = re.compile(r"^[A-Za-z0-9._-]+$")
_RUTA_RELATIVA_PLANTILLA = "data/taam/procedimientos/{id}/protocolo.pdf"


class PdfProtocoloInvalidoError(ValueError):
    """PDF rechazado por validacion de contenido o nombre."""


def ruta_relativa_protocolo(tipo_id: uuid.UUID) -> str:
    """Ruta logica almacenada en BD (relativa al workspace)."""
    return _RUTA_RELATIVA_PLANTILLA.format(id=tipo_id)


def ruta_absoluta_protocolo(tipo_id: uuid.UUID) -> Path:
    """Ruta absoluta en disco para lectura/escritura."""
    return resolver_ruta_workspace(ruta_relativa_protocolo(tipo_id))


async def leer_y_validar_pdf(archivo: UploadFile, cfg: Configuracion) -> tuple[bytes, str]:
    """
    Lee el upload, valida MIME/nombre/tamano/magic bytes y devuelve bytes + nombre seguro.
    """
    nombre = (archivo.filename or "").strip()
    if not nombre:
        raise PdfProtocoloInvalidoError("El archivo PDF debe tener nombre.")
    base = Path(nombre).name
    if not _NOMBRE_ARCHIVO_PERMITIDO.fullmatch(base):
        raise PdfProtocoloInvalidoError(
            "El nombre del archivo solo puede contener letras ASCII, numeros, punto, guion y guion bajo."
        )

    content_type = (archivo.content_type or "").strip().lower()
    if content_type and content_type != "application/pdf":
        raise PdfProtocoloInvalidoError("El archivo debe ser application/pdf.")

    max_bytes = cfg.taam_pdf_max_mb * 1024 * 1024
    contenido = await archivo.read()
    if not contenido:
        raise PdfProtocoloInvalidoError("El archivo PDF esta vacio.")
    if len(contenido) > max_bytes:
        raise PdfProtocoloInvalidoError(
            f"El PDF supera el tamano maximo permitido ({cfg.taam_pdf_max_mb} MB)."
        )
    if not contenido.startswith(_PREFIJO_MAGIC_PDF):
        raise PdfProtocoloInvalidoError("El contenido no parece un PDF valido.")

    return contenido, base


def hash_sha256(contenido: bytes) -> str:
    """Hex digest SHA-256 del archivo."""
    return hashlib.sha256(contenido).hexdigest()


def guardar_pdf_en_disco(tipo_id: uuid.UUID, contenido: bytes) -> Path:
    """Escribe ``protocolo.pdf`` bajo ``data/taam/procedimientos/{id}/``."""
    destino = ruta_absoluta_protocolo(tipo_id)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    return destino


def http_422_desde_error_pdf(exc: PdfProtocoloInvalidoError) -> HTTPException:
    return HTTPException(
        status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )
