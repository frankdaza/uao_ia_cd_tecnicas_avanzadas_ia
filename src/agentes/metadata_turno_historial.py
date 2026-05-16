"""
Construccion y normalizacion de ``metadata_turno`` para historial M2 (TASK-94).

Se persiste en ``AIMessage.additional_kwargs`` junto a las claves legacy ``tool`` y
``fuentes`` usadas por versiones anteriores del grafo.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

_MAX_PENSAMIENTOS = 16
_MAX_FUENTES = 40
_MAX_RAZON_CARACTERES = 900
_MAX_ARG_VALOR_CARACTERES = 400
_MAX_ARGS_KEYS = 24
_MAX_METADATA_JSON_BYTES = 48_000

_CLAVES_PENSAMIENTO_PERMITIDAS = frozenset(
    {
        "tipo",
        "herramienta",
        "razon_breve",
        "argumentos_resumidos",
        "faq_umbral_match",
        "faq_match_encontrado",
        "faq_consulta_ejecutada",
    }
)

_CLAVES_FUENTE_PERMITIDAS = frozenset(
    {
        "archivo",
        "titulo",
        "source_url",
        "score",
        "score_denso",
        "score_final",
        "chunk_index",
    }
)


def _truncar_texto(valor: str, maximo: int) -> str:
    if len(valor) <= maximo:
        return valor
    return valor[: maximo - 1] + "…"


def _sanear_argumentos_resumidos(valor: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for i, (clave, raw) in enumerate(valor.items()):
        if i >= _MAX_ARGS_KEYS:
            break
        sk = str(clave)[:128]
        if isinstance(raw, str):
            out[sk] = _truncar_texto(raw, _MAX_ARG_VALOR_CARACTERES)
        elif isinstance(raw, (int, float, bool)) or raw is None:
            out[sk] = raw
        elif isinstance(raw, dict):
            out[sk] = _sanear_argumentos_resumidos(
                {str(k)[:64]: v for k, v in list(raw.items())[:12]}
            )
        else:
            out[sk] = _truncar_texto(str(raw), _MAX_ARG_VALOR_CARACTERES)
    return out


def _sanear_pensamiento(item: dict[str, Any]) -> dict[str, Any]:
    salida: dict[str, Any] = {}
    for clave in _CLAVES_PENSAMIENTO_PERMITIDAS:
        if clave not in item:
            continue
        valor = item[clave]
        if clave == "argumentos_resumidos" and isinstance(valor, dict):
            salida[clave] = _sanear_argumentos_resumidos(valor)
        elif clave == "razon_breve" and isinstance(valor, str):
            salida[clave] = _truncar_texto(valor, _MAX_RAZON_CARACTERES)
        elif clave == "faq_consulta_ejecutada" and isinstance(valor, str):
            salida[clave] = _truncar_texto(valor, _MAX_ARG_VALOR_CARACTERES)
        elif clave in ("faq_umbral_match", "faq_match_encontrado"):
            salida[clave] = valor
        elif clave in ("tipo", "herramienta") and valor is not None:
            salida[clave] = str(valor)[:256]
    return salida


def _sanear_fuente(item: dict[str, Any]) -> dict[str, Any]:
    salida: dict[str, Any] = {}
    for clave in _CLAVES_FUENTE_PERMITIDAS:
        if clave not in item:
            continue
        valor = item[clave]
        if clave == "source_url" and isinstance(valor, str):
            salida[clave] = _truncar_texto(valor, 2048)
        elif clave in ("archivo", "titulo") and isinstance(valor, str):
            salida[clave] = _truncar_texto(valor, 1024)
        elif clave in ("score", "score_denso", "score_final") and isinstance(
            valor, (int, float)
        ):
            salida[clave] = float(valor)
        elif clave == "chunk_index" and isinstance(valor, int):
            salida[clave] = valor
    return salida


def _tamano_json_aprox(objeto: Any) -> int:
    try:
        return len(json.dumps(objeto, ensure_ascii=False, default=str))
    except (TypeError, ValueError):
        return _MAX_METADATA_JSON_BYTES + 1


def construir_metadata_turno_para_persistencia(state: dict[str, Any]) -> dict[str, Any]:
    """
    Arma el dict ``metadata_turno`` a guardar en ``additional_kwargs`` del AIMessage.

    Incluye herramienta efectiva, pensamientos sanados y fuentes RAG acotadas.
    """
    herramienta = state.get("tool_decidida")
    herr_txt = str(herramienta) if herramienta is not None else None

    pens_raw = state.get("pensamientos") or []
    pens_saneados: list[dict[str, Any]] = []
    if isinstance(pens_raw, list):
        for p in pens_raw[:_MAX_PENSAMIENTOS]:
            if isinstance(p, dict):
                pens_saneados.append(_sanear_pensamiento(p))

    fuentes_raw = state.get("fuentes") or []
    fuentes_saneadas: list[dict[str, Any]] = []
    if isinstance(fuentes_raw, list):
        for f in fuentes_raw[:_MAX_FUENTES]:
            if isinstance(f, dict):
                fuentes_saneadas.append(_sanear_fuente(f))

    meta: dict[str, Any] = {
        "motor": "agente",
        "herramienta_efectiva": herr_txt,
        "pensamientos": pens_saneados,
        "fuentes": fuentes_saneadas,
        "recortado": False,
    }

    while pens_saneados and _tamano_json_aprox(meta) > _MAX_METADATA_JSON_BYTES:
        pens_saneados.pop()
        meta["pensamientos"] = pens_saneados
        meta["recortado"] = True

    while fuentes_saneadas and _tamano_json_aprox(meta) > _MAX_METADATA_JSON_BYTES:
        fuentes_saneadas.pop()
        meta["fuentes"] = fuentes_saneadas
        meta["recortado"] = True

    return meta


def _legacy_metadata_desde_kwargs(kwargs: dict[str, Any]) -> dict[str, Any] | None:
    tool = kwargs.get("tool")
    fuentes = kwargs.get("fuentes")
    herr_txt = str(tool) if tool is not None else None
    fuentes_list: list[dict[str, Any]] = []
    if isinstance(fuentes, list):
        for f in fuentes:
            if isinstance(f, dict):
                fuentes_list.append(_sanear_fuente(f))
    if herr_txt is None and not fuentes_list:
        return None
    return {
        "motor": "agente",
        "herramienta_efectiva": herr_txt,
        "pensamientos": [],
        "fuentes": fuentes_list,
        "recortado": None,
    }


def normalizar_metadata_turno_desde_additional_kwargs(
    kwargs: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Obtiene un ``metadata_turno`` estable para la API desde ``additional_kwargs``.

    Acepta el formato nuevo (clave ``metadata_turno``) o el legacy (``tool`` / ``fuentes``).
    """
    if not kwargs:
        return None
    raw = kwargs.get("metadata_turno")
    if isinstance(raw, dict):
        base = deepcopy(raw)
        pens = base.get("pensamientos")
        if isinstance(pens, list):
            base["pensamientos"] = [
                _sanear_pensamiento(p) if isinstance(p, dict) else {}
                for p in pens[:_MAX_PENSAMIENTOS]
            ]
        else:
            base["pensamientos"] = []
        fnts = base.get("fuentes")
        if isinstance(fnts, list):
            base["fuentes"] = [
                _sanear_fuente(f) if isinstance(f, dict) else {}
                for f in fnts[:_MAX_FUENTES]
            ]
        else:
            base["fuentes"] = []
        if base.get("motor") is None:
            base["motor"] = "agente"
        return base
    return _legacy_metadata_desde_kwargs(kwargs)
