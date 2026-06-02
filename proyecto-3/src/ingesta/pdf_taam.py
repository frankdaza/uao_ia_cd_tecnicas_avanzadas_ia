"""Extraccion de texto desde PDFs TAAM."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)

_MIN_CARACTERES_TEXTO = 40


def normalizar_espacios(texto: str) -> str:
    """Colapsa espacios en blanco y recorta extremos."""
    return re.sub(r"\s+", " ", texto).strip()


def extraer_texto_pdf(ruta: Path) -> str | None:
    """
    Extrae texto concatenado del PDF.

    Retorna ``None`` si no hay texto util (menos de ``_MIN_CARACTERES_TEXTO``).
    """
    lector = PdfReader(str(ruta))
    partes: list[str] = []
    for pagina in lector.pages:
        fragmento = pagina.extract_text() or ""
        fragmento = fragmento.strip()
        if fragmento:
            partes.append(fragmento)
    texto = normalizar_espacios(" ".join(partes))
    if len(texto) < _MIN_CARACTERES_TEXTO:
        logger.warning(
            "PDF sin texto extraible (omitido): %s (caracteres=%s)",
            ruta,
            len(texto),
        )
        return None
    return texto
