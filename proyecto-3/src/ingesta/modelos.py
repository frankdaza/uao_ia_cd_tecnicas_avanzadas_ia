"""Modelos de datos para la ingesta OpenFang."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChunkPlanificado:
    """Fragmento listo para insertar en ``memories``."""

    source_id: str
    content_hash: str
    memory_id: str
    texto: str
    tipo_fuente: str
    ruta_relativa: str
    titulo: str
    chunk_index: int


@dataclass
class EstadisticasIngesta:
    """Contadores al cerrar una corrida."""

    archivos_markdown: int = 0
    archivos_pdf: int = 0
    archivos_omitidos: int = 0
    chunks_planificados: int = 0
    chunks_insertados: int = 0
    chunks_actualizados: int = 0
    chunks_omitidos: int = 0
    advertencias: list[str] = field(default_factory=list)
