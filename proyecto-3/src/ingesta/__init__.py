"""Ingesta de corpus workspace hacia memoria semantica OpenFang (SQLite)."""

from src.ingesta.fragmentar import fragmentar
from src.ingesta.modelos import ChunkPlanificado, EstadisticasIngesta

__all__ = [
    "ChunkPlanificado",
    "EstadisticasIngesta",
    "fragmentar",
]
