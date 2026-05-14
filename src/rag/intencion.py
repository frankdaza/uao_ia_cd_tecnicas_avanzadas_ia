"""
Heuristica pura de intencion de consulta (sin LLM) para enrutar recuperacion adaptativa.

Prioridad documentada: **conteo** > **listado** > **factual**.
"""

from __future__ import annotations

import re
from typing import Literal

IntencionConsulta = Literal["factual", "listado", "conteo"]

# Conteo: plural "cuantos/cuantas" evita confundir con "cuanto cuesta" (singular).
_RE_CONTEO = re.compile(
    r"\b(cu[aá]ntos|cu[aá]ntas|n[uú]mero\s+de|cantidad\s+de)\b",
    re.IGNORECASE,
)
_RE_LISTADO = re.compile(
    r"\b(lista|listados?|enumera|dame\s+todos|dame\s+todas|todos?\s+los|todas?\s+las|"
    r"qu[eé]\s+m[eé]dicos)\b",
    re.IGNORECASE,
)


def inferir_intencion(consulta: str) -> IntencionConsulta:
    """
    Clasifica la consulta en factual (defecto), listado o conteo.

    Orden de evaluacion: primero conteo, luego listado; si no coincide, factual.
    """
    texto = (consulta or "").strip()
    if not texto:
        return "factual"
    if _RE_CONTEO.search(texto):
        return "conteo"
    if _RE_LISTADO.search(texto):
        return "listado"
    return "factual"


_RE_MISION_VISION = re.compile(
    r"\b(misi[oó]n|visi[oó]n\s+institucional|visi[oó]n\s+y\s+misi[oó]n)\b",
    re.IGNORECASE,
)


def inferir_filtros_tipo_pagina_para_rag(consulta: str) -> list[str] | None:
    """
    Filtro blando opcional para ``rag_denso`` cuando la consulta apunta a paginas institucionales.

    Retorna ``None`` si no aplica (comportamiento identico al RAG sin filtro).
    """
    t = (consulta or "").strip()
    if not t:
        return None
    if _RE_MISION_VISION.search(t):
        return ["institucional"]
    return None
