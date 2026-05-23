"""Descubrimiento de fuentes Markdown y PDF en el workspace."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.ingesta.fragmentar import fragmentar
from src.ingesta.idempotencia import (
    calcular_content_hash,
    memory_id_desde_source_id,
    ruta_relativa_workspace,
    source_id_markdown,
    source_id_taam_pdf,
)
from src.ingesta.markdown import leer_markdown, titulo_desde_meta
from src.ingesta.modelos import ChunkPlanificado
from src.ingesta.pdf_taam import extraer_texto_pdf

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpcionesFuentes:
    """Filtros de descubrimiento."""

    incluir_markdown: bool = True
    incluir_pdf: bool = True
    limite_archivos: int | None = None


def listar_markdown(raiz_markdown: Path) -> list[Path]:
    if not raiz_markdown.is_dir():
        return []
    return sorted(raiz_markdown.rglob("*.md"))


def listar_pdfs(raiz_taam: Path) -> list[Path]:
    if not raiz_taam.is_dir():
        return []
    return sorted(raiz_taam.rglob("*.pdf"))


def _aplicar_limite(rutas: list[Path], limite: int | None) -> list[Path]:
    if limite is None or limite <= 0:
        return rutas
    return rutas[:limite]


def planificar_chunks_markdown(
    rutas: list[Path],
    raiz_workspace: Path,
    *,
    tam_chunk: int = 1000,
    solape: int = 150,
) -> tuple[list[ChunkPlanificado], int]:
    """Genera chunks desde archivos ``.md``."""
    salida: list[ChunkPlanificado] = []
    omitidos = 0
    for ruta in rutas:
        meta, cuerpo = leer_markdown(ruta)
        if not cuerpo:
            omitidos += 1
            continue
        rel = ruta_relativa_workspace(ruta, raiz_workspace)
        titulo = titulo_desde_meta(meta, ruta)
        partes = fragmentar(cuerpo, tam=tam_chunk, solape=solape)
        if not partes:
            omitidos += 1
            continue
        for indice, texto in enumerate(partes):
            sid = source_id_markdown(rel, indice)
            salida.append(
                ChunkPlanificado(
                    source_id=sid,
                    content_hash=calcular_content_hash(texto),
                    memory_id=memory_id_desde_source_id(sid),
                    texto=texto,
                    tipo_fuente="markdown",
                    ruta_relativa=rel,
                    titulo=titulo,
                    chunk_index=indice,
                )
            )
    return salida, omitidos


def planificar_chunks_pdf(
    rutas: list[Path],
    raiz_workspace: Path,
    *,
    tam_chunk: int = 1000,
    solape: int = 150,
) -> tuple[list[ChunkPlanificado], int]:
    """Genera chunks desde PDFs; omite archivos sin texto."""
    salida: list[ChunkPlanificado] = []
    omitidos = 0
    for ruta in rutas:
        texto = extraer_texto_pdf(ruta)
        if texto is None:
            omitidos += 1
            continue
        rel = ruta_relativa_workspace(ruta, raiz_workspace)
        titulo = ruta.stem.replace("-", " ").strip()
        partes = fragmentar(texto, tam=tam_chunk, solape=solape)
        for indice, fragmento in enumerate(partes):
            sid = source_id_taam_pdf(rel, indice)
            salida.append(
                ChunkPlanificado(
                    source_id=sid,
                    content_hash=calcular_content_hash(fragmento),
                    memory_id=memory_id_desde_source_id(sid),
                    texto=fragmento,
                    tipo_fuente="taam_pdf",
                    ruta_relativa=rel,
                    titulo=titulo,
                    chunk_index=indice,
                )
            )
    return salida, omitidos


def planificar_todas_las_fuentes(
    raiz_workspace: Path,
    opciones: OpcionesFuentes,
    *,
    tam_chunk: int = 1000,
    solape: int = 150,
) -> tuple[list[ChunkPlanificado], int, int, int]:
    """
    Planifica chunks de Markdown y PDF.

    Retorna ``(chunks, n_md, n_pdf, omitidos)``.
    """
    rutas_md: list[Path] = []
    rutas_pdf: list[Path] = []
    if opciones.incluir_markdown:
        rutas_md = _aplicar_limite(
            listar_markdown(raiz_workspace / "data" / "markdown"),
            opciones.limite_archivos,
        )
    if opciones.incluir_pdf:
        rutas_pdf = _aplicar_limite(
            listar_pdfs(raiz_workspace / "data" / "taam"),
            opciones.limite_archivos,
        )

    chunks_md, omit_md = planificar_chunks_markdown(
        rutas_md, raiz_workspace, tam_chunk=tam_chunk, solape=solape
    )
    chunks_pdf, omit_pdf = planificar_chunks_pdf(
        rutas_pdf, raiz_workspace, tam_chunk=tam_chunk, solape=solape
    )
    return (
        chunks_md + chunks_pdf,
        len(rutas_md),
        len(rutas_pdf),
        omit_md + omit_pdf,
    )
