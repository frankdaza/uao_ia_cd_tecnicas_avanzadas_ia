"""Expansion simple de queries con sinonimos lexicos para BM25 (solo la pregunta)."""

from __future__ import annotations

import re
from unicodedata import category, normalize


def _nfkd_sin_tildes_mayusc(texto: str) -> str:
    """Versión estable para igualar contra claves ascii (sin grafía compleja)."""
    ascii_up = "".join(ch for ch in normalize("NFKD", texto.casefold()) if category(ch) != "Mn")
    return ascii_up


# Concepto en ascii simple -> expansiones opcionales (tokens libres BM25 despues tokenizar/stemming).
_TERMINO_EXPANSION: dict[str, tuple[str, ...]] = {
    "cita": ("agendar", "agendamiento", "consulta", "consultar"),
    "medico": ("doctor", "doctora",),
    "doctor": ("medico", "medica",),
    "telefono": ("contacto", "linea", "llamada"),
    "paciente": ("usuario", "asistencia"),
}

_RX_PALABRA = re.compile(r"\w+", flags=re.UNICODE)


def expandir_query(pregunta: str) -> str:
    """
    Concatena sinonimos cuando aparecen vocablos relacionados por un diccionario chico.

    Solo aplica a la pregunta; no replica en los documentos (MVP BM25 lexical).
    """
    partes_adjuntas: list[str] = []
    apilados: set[str] = set()
    for parte in _RX_PALABRA.findall(pregunta):
        if len(parte) < 2:
            continue
        clave_busqueda = _nfkd_sin_tildes_mayusc(parte)
        extras = _TERMINO_EXPANSION.get(clave_busqueda)
        if not extras:
            continue
        for x in extras:
            if x not in apilados:
                partes_adjuntas.append(x)
                apilados.add(x)
    if not partes_adjuntas:
        return pregunta
    return pregunta + " " + " ".join(partes_adjuntas)


__all__: tuple[str, ...] = ("expandir_query",)
