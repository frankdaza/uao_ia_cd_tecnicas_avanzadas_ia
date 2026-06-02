"""Extraccion de texto desde protocolos PDF (pdfplumber)."""

from __future__ import annotations

from pathlib import Path

import pdfplumber
from langchain_core.documents import Document


def extraer_documentos_desde_pdf(ruta: Path) -> tuple[list[Document], int]:
    """
    Extrae texto pagina a pagina con pdfplumber.

    Retorna documentos LangChain y el numero de paginas procesadas.
    """
    documentos: list[Document] = []
    paginas = 0
    nombre_archivo = ruta.name
    with pdfplumber.open(ruta) as pdf:
        for indice, pagina in enumerate(pdf.pages, start=1):
            paginas += 1
            texto = (pagina.extract_text() or "").strip()
            if not texto:
                continue
            documentos.append(
                Document(
                    page_content=texto,
                    metadata={"pagina": indice, "nombre_archivo": nombre_archivo},
                )
            )
    return documentos, paginas
