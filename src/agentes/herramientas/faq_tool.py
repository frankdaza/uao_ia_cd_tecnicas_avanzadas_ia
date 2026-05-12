"""
Tool determinista de FAQs estructuradas (JSON) sin LLM ni Qdrant.

El score por FAQ es la proporción de palabras clave que coinciden respecto al
total de palabras clave de esa entrada: ``coincidencias / len(keywords)``.
Una palabra clave coincide si, tras normalizar (NFKD sin marcas diacríticas,
minúsculas) y tokenizar la consulta y la clave, **cada** token obtenido de la
clave aparece como token en la consulta (subconjunto estricto de tokens).
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.api.configuracion import obtener_configuracion

_RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
_RUTA_JSON_POR_DEFECTO = _RAIZ_PROYECTO / "data" / "structured" / "faqs.json"

# Cache (mtime_ns, lista de entradas) para invalidar si el archivo cambia en disco.
_cache_entradas: tuple[int, list["FaqEntrada"]] | None = None


class ArchivoFaqStructuredAusenteError(FileNotFoundError):
    """El JSON de FAQs estructuradas no existe o no es accesible."""


class FaqEntrada(BaseModel):
    """Una fila del archivo ``faqs.json`` validado contra el schema del proyecto."""

    id: str
    intent: str
    keywords: list[str]
    pregunta_canonica: str
    respuesta: str
    actualizado_el: str
    source_url: str | None = None


class FaqRespuesta(BaseModel):
    """Respuesta expuesta al router cuando hay match por umbral."""

    id: str
    intent: str
    pregunta_canonica: str
    respuesta: str
    source_url: str | None = None


class ArgsConsultaFaq(BaseModel):
    """Argumentos de la StructuredTool expuesta al modelo."""

    consulta: str = Field(
        description=(
            "Pregunta o mensaje del usuario en español sobre datos institucionales "
            "factuales (teléfonos, horarios, NIT, dirección, correos, sitio web, etc.)."
        ),
        min_length=1,
    )


@dataclass(frozen=True)
class _CandidatoScore:
    entrada: FaqEntrada
    score: float
    coincidencias: int


def _normalizar_sin_tildes(texto: str) -> str:
    nkfd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nkfd if not unicodedata.combining(c)).lower()


def _tokens_desde_fragmento(fragmento: str) -> list[str]:
    """Tokens alfanuméricos e hífen interno (p. ej. ``18-49``) dentro de un fragmento ya normalizado."""
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", fragmento)


def _tokens_consulta(consulta: str) -> set[str]:
    base = _normalizar_sin_tildes(consulta)
    return set(_tokens_desde_fragmento(base))


def _tokens_palabra_clave(palabra_clave: str) -> list[str]:
    """Tokens requeridos para considerar una palabra clave como encontrada."""
    norm = _normalizar_sin_tildes(palabra_clave)
    salida: list[str] = []
    for parte in norm.split():
        salida.extend(_tokens_desde_fragmento(parte))
    return salida


def _palabra_clave_coincide(palabra_clave: str, tokens_consulta: set[str]) -> bool:
    req = _tokens_palabra_clave(palabra_clave)
    return bool(req) and all(t in tokens_consulta for t in req)


def _resolver_ruta_json() -> Path:
    cfg = obtener_configuracion()
    rel = Path(cfg.faq_json_relativo_raiz)
    return rel if rel.is_absolute() else _RAIZ_PROYECTO / rel


def invalidar_cache_faqs() -> None:
    """Limpia la cache en memoria (útil en tests tras cambiar el archivo o la config)."""
    global _cache_entradas
    _cache_entradas = None


def _cargar_entradas_desde_disco() -> list[FaqEntrada]:
    global _cache_entradas
    ruta = _resolver_ruta_json()
    if not ruta.is_file():
        raise ArchivoFaqStructuredAusenteError(
            "No se encontró el archivo de FAQs estructuradas en "
            f"{ruta}. Verifique la ruta, el despliegue del repositorio o la variable "
            "FAQ_JSON_RELATIVO_RAIZ."
        )
    mtime_ns = ruta.stat().st_mtime_ns
    if _cache_entradas is not None and _cache_entradas[0] == mtime_ns:
        return _cache_entradas[1]
    with ruta.open(encoding="utf-8") as f:
        payload: dict[str, Any] = json.load(f)
    lista = payload.get("faqs")
    if not isinstance(lista, list):
        raise ValueError("El JSON de FAQs debe contener la clave 'faqs' con una lista.")
    entradas = [FaqEntrada.model_validate(item) for item in lista]
    _cache_entradas = (mtime_ns, entradas)
    return entradas


def buscar_faq(consulta: str) -> FaqRespuesta | None:
    """
    Busca la FAQ con mayor score de solapamiento de palabras clave.

    Score: ``(# palabras clave que coinciden) / (# palabras clave de la FAQ)``.
    Se retorna la mejor entrada si su score es ``>= FAQ_UMBRAL_MATCH``; si no, ``None``.
    En empate de score, gana la que tenga más coincidencias absolutas y luego ``id`` menor
    en orden lexicográfico (orden estable).
    """
    umbral = obtener_configuracion().faq_umbral_match
    entradas = _cargar_entradas_desde_disco()
    tokens_q = _tokens_consulta(consulta)
    candidatos: list[_CandidatoScore] = []
    for entrada in entradas:
        if not entrada.keywords:
            continue
        n = len(entrada.keywords)
        coincidencias = sum(1 for kw in entrada.keywords if _palabra_clave_coincide(kw, tokens_q))
        score = coincidencias / n
        if score >= umbral:
            candidatos.append(_CandidatoScore(entrada=entrada, score=score, coincidencias=coincidencias))
    if not candidatos:
        return None
    mejor = min(
        candidatos,
        key=lambda c: (-c.score, -c.coincidencias, c.entrada.id),
    )
    e = mejor.entrada
    return FaqRespuesta(
        id=e.id,
        intent=e.intent,
        pregunta_canonica=e.pregunta_canonica,
        respuesta=e.respuesta,
        source_url=e.source_url,
    )


def _ejecutar_tool_faq(consulta: str) -> dict[str, Any]:
    hallazgo = buscar_faq(consulta)
    if hallazgo is None:
        return {"encontrado": False, "detalle": "Ninguna FAQ superó el umbral de coincidencia."}
    return {"encontrado": True, **hallazgo.model_dump(mode="json")}


def crear_faq_tool() -> StructuredTool:
    """
    Construye la StructuredTool ``faq_estructurada`` para tool binding / LangGraph.

    La ejecución solo lee ``data/structured/faqs.json`` (cache por ``mtime``) y aplica
    reglas deterministas; no usa Qdrant, LlamaIndex ni APIs de modelo dentro de la tool.
    """
    return StructuredTool.from_function(
        name="faq_estructurada",
        description=(
            "Resuelve preguntas frecuentes institucionales con respuesta determinista "
            "desde un JSON curado (teléfonos PBX, horarios SIAU/PQRS, NIT, dirección en Cali, "
            "correos, sitio web oficial, urgencias pediátricas, portal de resultados, etc.). "
            "Úsala cuando el usuario pida datos concretos publicados por la institución y no "
            "requiera razonamiento clínico ni documentación amplia del corpus."
        ),
        func=_ejecutar_tool_faq,
        args_schema=ArgsConsultaFaq,
        infer_schema=False,
    )
