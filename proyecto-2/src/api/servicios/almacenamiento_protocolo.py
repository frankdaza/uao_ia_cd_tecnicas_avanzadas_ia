"""Validacion y almacenamiento de protocolos TAAM (PDF o Markdown) en el workspace."""

from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path
from typing import Literal

import yaml
from fastapi import HTTPException, UploadFile
from fastapi import status as estado_http

from src.configuracion import Configuracion
from src.rutas_workspace import resolver_ruta_workspace

FormatoProtocolo = Literal["pdf", "markdown"]

_PREFIJO_MAGIC_PDF = b"%PDF"
_NOMBRE_ARCHIVO_PERMITIDO = re.compile(r"^[A-Za-z0-9._-]+$")
_MIME_MARKDOWN_ACEPTADOS = frozenset(
    {
        "",
        "text/plain",
        "text/markdown",
        "text/x-markdown",
        "application/octet-stream",
    }
)


class ArchivoProtocoloInvalidoError(ValueError):
    """Archivo de protocolo rechazado por validacion de contenido o nombre."""


def ruta_relativa_protocolo(
    tipo_id: uuid.UUID,
    formato: FormatoProtocolo = "pdf",
) -> str:
    """Ruta logica almacenada en BD (relativa al workspace)."""
    nombre = "protocolo.pdf" if formato == "pdf" else "protocolo.md"
    return f"data/taam/procedimientos/{tipo_id}/{nombre}"


def ruta_absoluta_por_formato(tipo_id: uuid.UUID, formato: FormatoProtocolo) -> Path:
    """Ruta absoluta en disco para lectura/escritura."""
    return resolver_ruta_workspace(ruta_relativa_protocolo(tipo_id, formato))


def ruta_absoluta_protocolo(tipo_id: uuid.UUID) -> Path:
    """Compatibilidad: ruta al PDF canonico del procedimiento."""
    return ruta_absoluta_por_formato(tipo_id, "pdf")


def inferir_formato_desde_nombre(nombre: str) -> FormatoProtocolo:
    """Detecta formato por extension del nombre de archivo."""
    base = Path(nombre).name.lower()
    if base.endswith(".pdf"):
        return "pdf"
    if base.endswith(".md"):
        return "markdown"
    raise ArchivoProtocoloInvalidoError(
        "El archivo debe tener extension .pdf o .md."
    )


def parsear_markdown_protocolo(texto: str) -> tuple[dict[str, object], str]:
    """
    Separa front matter YAML opcional del cuerpo Markdown.

    YAML invalido o delimitadores mal cerrados lanzan ``ArchivoProtocoloInvalidoError``.
    """
    texto = texto.lstrip("\ufeff")
    if not texto.startswith("---\n"):
        return {}, texto
    resto = texto[4:]
    fin = resto.find("\n---\n")
    if fin <= 0:
        raise ArchivoProtocoloInvalidoError("Front matter Markdown mal cerrado.")
    bloque = resto[:fin]
    cuerpo = resto[fin + 5 :]
    try:
        meta = yaml.safe_load(bloque) or {}
    except yaml.YAMLError as exc:
        raise ArchivoProtocoloInvalidoError(
            f"Front matter YAML invalido: {exc}"
        ) from exc
    if not isinstance(meta, dict):
        raise ArchivoProtocoloInvalidoError("Front matter debe ser un mapa YAML.")
    return meta, cuerpo


def _validar_nombre_archivo(nombre: str) -> str:
    if not nombre:
        raise ArchivoProtocoloInvalidoError("El archivo de protocolo debe tener nombre.")
    base = Path(nombre).name
    if not _NOMBRE_ARCHIVO_PERMITIDO.fullmatch(base):
        raise ArchivoProtocoloInvalidoError(
            "El nombre del archivo solo puede contener letras ASCII, numeros, punto, guion y guion bajo."
        )
    return base


def _limite_bytes(cfg: Configuracion) -> int:
    return cfg.taam_pdf_max_mb * 1024 * 1024


async def _leer_contenido_upload(archivo: UploadFile, cfg: Configuracion) -> tuple[bytes, str]:
    nombre = _validar_nombre_archivo((archivo.filename or "").strip())
    max_bytes = _limite_bytes(cfg)
    contenido = await archivo.read()
    if not contenido:
        raise ArchivoProtocoloInvalidoError("El archivo de protocolo esta vacio.")
    if len(contenido) > max_bytes:
        raise ArchivoProtocoloInvalidoError(
            f"El archivo supera el tamano maximo permitido ({cfg.taam_pdf_max_mb} MB)."
        )
    return contenido, nombre


async def _validar_pdf(contenido: bytes, nombre: str, archivo: UploadFile, cfg: Configuracion) -> None:
    content_type = (archivo.content_type or "").strip().lower()
    if content_type and content_type != "application/pdf":
        raise ArchivoProtocoloInvalidoError("El archivo debe ser application/pdf.")
    if not contenido.startswith(_PREFIJO_MAGIC_PDF):
        raise ArchivoProtocoloInvalidoError("El contenido no parece un PDF valido.")


async def _validar_markdown(contenido: bytes, nombre: str, archivo: UploadFile) -> None:
    if b"\x00" in contenido:
        raise ArchivoProtocoloInvalidoError("El Markdown no puede contener bytes nulos.")
    content_type = (archivo.content_type or "").strip().lower()
    if content_type not in _MIME_MARKDOWN_ACEPTADOS:
        raise ArchivoProtocoloInvalidoError(
            "Tipo MIME no admitido para Markdown; use text/plain o text/markdown."
        )
    try:
        texto = contenido.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ArchivoProtocoloInvalidoError(
            "El archivo Markdown debe estar codificado en UTF-8."
        ) from exc
    parsear_markdown_protocolo(texto)


async def leer_y_validar_archivo_protocolo(
    archivo: UploadFile,
    cfg: Configuracion,
) -> tuple[bytes, str, FormatoProtocolo]:
    """Lee el upload y valida segun extension (.pdf o .md)."""
    contenido, nombre = await _leer_contenido_upload(archivo, cfg)
    formato = inferir_formato_desde_nombre(nombre)
    if formato == "pdf":
        await _validar_pdf(contenido, nombre, archivo, cfg)
    else:
        await _validar_markdown(contenido, nombre, archivo)
    return contenido, nombre, formato


def hash_sha256(contenido: bytes) -> str:
    """Hex digest SHA-256 del archivo."""
    return hashlib.sha256(contenido).hexdigest()


def guardar_protocolo_en_disco(
    tipo_id: uuid.UUID,
    contenido: bytes,
    formato: FormatoProtocolo,
    *,
    ruta_anterior: str | None = None,
) -> Path:
    """Escribe el protocolo activo y elimina el archivo previo si cambia de formato o ruta."""
    destino = ruta_absoluta_por_formato(tipo_id, formato)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    if ruta_anterior:
        anterior = resolver_ruta_workspace(ruta_anterior)
        if anterior.is_file() and anterior.resolve() != destino.resolve():
            anterior.unlink(missing_ok=True)
    return destino


def guardar_pdf_en_disco(tipo_id: uuid.UUID, contenido: bytes) -> Path:
    """Compatibilidad: guarda solo PDF sin limpiar otro formato."""
    return guardar_protocolo_en_disco(tipo_id, contenido, "pdf")


async def leer_y_validar_pdf(archivo: UploadFile, cfg: Configuracion) -> tuple[bytes, str]:
    """Compatibilidad: solo acepta uploads PDF."""
    contenido, nombre, formato = await leer_y_validar_archivo_protocolo(archivo, cfg)
    if formato != "pdf":
        raise ArchivoProtocoloInvalidoError("Se esperaba un archivo PDF.")
    return contenido, nombre


def http_422_desde_error_protocolo(exc: ArchivoProtocoloInvalidoError) -> HTTPException:
    return HTTPException(
        status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


def http_422_desde_error_pdf(exc: ArchivoProtocoloInvalidoError) -> HTTPException:
    """Alias de compatibilidad con imports legacy."""
    return http_422_desde_error_protocolo(exc)
