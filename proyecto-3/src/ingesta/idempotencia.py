"""Identificadores estables e idempotencia por hash de contenido."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

_NAMESPACE_INGESTA = uuid.UUID("00000000-0000-5000-8000-000000000002")


def calcular_content_hash(texto: str) -> str:
    """Hash SHA-256 hex del texto del chunk."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def memory_id_desde_source_id(source_id: str) -> str:
    """UUID determinista para fila ``memories.id``."""
    return str(uuid.uuid5(_NAMESPACE_INGESTA, source_id))


def source_id_markdown(ruta_relativa: str, indice: int) -> str:
    return f"markdown:{ruta_relativa}:{indice}"


def source_id_taam_pdf(ruta_relativa: str, indice: int) -> str:
    return f"taam-pdf:{ruta_relativa}:{indice}"


def ruta_relativa_workspace(ruta: Path, raiz_workspace: Path) -> str:
    """Ruta POSIX relativa al workspace."""
    try:
        return ruta.resolve().relative_to(raiz_workspace.resolve()).as_posix()
    except ValueError:
        return ruta.resolve().as_posix()
