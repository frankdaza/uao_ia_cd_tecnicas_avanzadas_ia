"""
Heuristicas para derivar filtros de ``listar_estructurado`` desde texto de usuario (sin LLM).
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.rag.runtime.intencion import texto_sugiere_foco_sedes_institucional

# Alineado con ``src.rag.runtime.extractor_metadata`` (sedes conocidas en el sitio).
_SEDES_ORDENADAS: tuple[str, ...] = (
    "Sede Valle del Lili",
    "Sede Av. Estación",
    "Sede Alfaguara",
    "Sede Limonar",
    "Sede Ciudad Jardin",
    "Sede Caicedonia",
    "Sede Tequendama",
)


_RE_CTX_MEDICO_DIR = re.compile(
    r"\b(directorio|medico|medicos|doctor|doctores|pediatras?|especialistas?|fichas?)\b",
    re.IGNORECASE,
)


def _sin_tildes(texto: str) -> str:
    nk = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nk if unicodedata.category(c) != "Mn")


@lru_cache(maxsize=1)
def _cargar_especialidades_canonicas() -> tuple[str, ...]:
    ruta = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "eval"
        / "especialidades_canonicas.json"
    )
    if not ruta.is_file():
        return ()
    try:
        raw = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    if not isinstance(raw, list):
        return ()
    out: list[str] = []
    for x in raw:
        if isinstance(x, str) and x.strip():
            out.append(x.strip())
    return tuple(out)


def _normalizar_busqueda(texto: str) -> str:
    return _sin_tildes(texto.lower())


def _detectar_sedes(pregunta: str) -> list[str]:
    n = _normalizar_busqueda(pregunta)
    halladas: list[str] = []
    for sede in _SEDES_ORDENADAS:
        if _normalizar_busqueda(sede) in n:
            halladas.append(sede)
    return halladas


def _detectar_especialidad_exacta(pregunta: str) -> str | None:
    n = _normalizar_busqueda(pregunta)
    for esp in _cargar_especialidades_canonicas():
        if _normalizar_busqueda(esp) in n:
            return esp
    return None


_RE_PED = re.compile(r"pediatr", re.IGNORECASE)
_RE_ONC = re.compile(r"oncolog", re.IGNORECASE)
_RE_CARD = re.compile(r"cardiolog", re.IGNORECASE)
_RE_GASTRO_PE = re.compile(r"gastro\s*ped|gastro\s*pedi", re.IGNORECASE)


def _detectar_especialidad_por_alias(pregunta: str) -> str | None:
    """Si no hubo match literal con el JSON canonico, usa alias frecuentes."""
    n = _normalizar_busqueda(pregunta)
    if _RE_GASTRO_PE.search(n):
        return "Gastroenterologia Pediatrica"
    if _RE_PED.search(n):
        return "Pediatria"
    if _RE_ONC.search(n):
        return "Oncologia"
    if _RE_CARD.search(n):
        return "Cardiologia"
    return None


def extraer_filtros_listado_desde_pregunta(pregunta: str) -> dict[str, Any]:
    """
    Construye un dict de filtros para :class:`src.rag.runtime.recuperador_listados.RecuperadorListados`.

    Claves posibles: ``tipo_pagina`` (str), ``especialidad`` (str), ``sedes`` (list[str]),
    ``especialidad_contains`` (str). Puede quedar vacio si no hay señales claras.
    """
    t = (pregunta or "").strip()
    out: dict[str, Any] = {}
    if not t:
        return out

    n = _normalizar_busqueda(t)
    if "servicio" in n and ("oncolog" in n or "lista" in n or "todos" in n):
        out["tipo_pagina"] = "servicio"
        if "oncolog" in t.lower():
            out["especialidad_contains"] = "oncolog"
        esp = _detectar_especialidad_exacta(t) or _detectar_especialidad_por_alias(t)
        if esp:
            out["especialidad"] = esp
        return out

    if _RE_CTX_MEDICO_DIR.search(n):
        out["tipo_pagina"] = "ficha_medico"
        sedes = _detectar_sedes(t)
        if sedes:
            out["sedes"] = sedes
        esp = _detectar_especialidad_exacta(t) or _detectar_especialidad_por_alias(t)
        if esp:
            out["especialidad"] = esp
        return out

    if texto_sugiere_foco_sedes_institucional(t):
        return {"tipo_pagina": "sede"}

    sedes = _detectar_sedes(t)
    if sedes:
        out["sedes"] = sedes

    esp = _detectar_especialidad_exacta(t) or _detectar_especialidad_por_alias(t)
    if esp:
        out["especialidad"] = esp

    return out


def especialidades_que_contienen(subcadena: str) -> list[str]:
    """Lista valores canonicos cuyo nombre contiene ``subcadena`` (sin tildes, casefold)."""
    sub = _normalizar_busqueda(subcadena)
    if len(sub) < 3:
        return []
    return [
        e for e in _cargar_especialidades_canonicas() if sub in _normalizar_busqueda(e)
    ]
