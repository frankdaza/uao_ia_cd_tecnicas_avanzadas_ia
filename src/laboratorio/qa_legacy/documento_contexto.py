"""Modelo neutro de documento de contexto para composicion de prompts (sin acoplamiento a recuperadores legacy)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentoContexto:
    """Fragmento o archivo Markdown enviado al modelo como parte del CONTEXTO."""

    ruta: Path
    titulo: str
    source_url: str
    contenido: str
    score: float
