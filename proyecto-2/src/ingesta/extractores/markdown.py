"""Extraccion de texto desde protocolos Markdown (UTF-8, front matter opcional)."""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from src.api.servicios.almacenamiento_protocolo import parsear_markdown_protocolo


def extraer_documentos_desde_markdown(ruta: Path) -> tuple[list[Document], int]:
    """
    Lee el archivo Markdown y produce un documento LangChain con el cuerpo util.

    Retorna documentos y ``1`` como unidad de pagina (un archivo = una unidad logica).
    """
    texto = ruta.read_text(encoding="utf-8")
    _meta, cuerpo = parsear_markdown_protocolo(texto)
    cuerpo = cuerpo.strip()
    if not cuerpo:
        return [], 1
    return [
        Document(
            page_content=cuerpo,
            metadata={"pagina": 1, "nombre_archivo": ruta.name},
        )
    ], 1
