"""Tool ``faq_postoperatorio`` sobre JSON estructurado."""

from __future__ import annotations

import json
from functools import lru_cache

from langchain_core.tools import tool

from src.agentes.tools.esquemas import EntradaFaqPostoperatorio
from src.rutas_workspace import resolver_ruta_workspace

_RUTA_FAQS = "data/structured/taam_faqs.json"
_MENSAJE_SIN_FAQ = (
    "No encontramos una respuesta frecuente para esa consulta. "
    "Por favor consulte a su equipo tratante."
)


@lru_cache
def _cargar_faqs() -> list[dict[str, object]]:
    ruta = resolver_ruta_workspace(_RUTA_FAQS)
    if not ruta.is_file():
        return []
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return list(datos.get("faqs", []))


def _puntuar_faq(consulta: str, faq: dict[str, object]) -> int:
    texto = consulta.lower()
    score = 0
    for kw in faq.get("keywords", []):
        if str(kw).lower() in texto:
            score += 2
    intent = str(faq.get("intent", "")).lower()
    if intent and intent.replace("_", " ") in texto:
        score += 3
    pregunta = str(faq.get("pregunta_canonica", "")).lower()
    if any(palabra in pregunta for palabra in texto.split() if len(palabra) > 4):
        score += 1
    return score


@tool("faq_postoperatorio", args_schema=EntradaFaqPostoperatorio)
def faq_postoperatorio(consulta: str) -> str:
    """
    Busca respuestas frecuentes de seguimiento postoperatorio en datos estructurados.

    No sustituye indicaciones personalizadas del cirujano.
    """
    faqs = _cargar_faqs()
    if not faqs:
        return _MENSAJE_SIN_FAQ

    mejor: dict[str, object] | None = None
    mejor_score = 0
    for faq in faqs:
        s = _puntuar_faq(consulta, faq)
        if s > mejor_score:
            mejor_score = s
            mejor = faq

    if mejor is None or mejor_score == 0:
        return _MENSAJE_SIN_FAQ

    return str(mejor.get("respuesta", _MENSAJE_SIN_FAQ))
