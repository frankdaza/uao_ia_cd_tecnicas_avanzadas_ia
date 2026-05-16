"""
Enumeracion por payload en Qdrant (scroll) sin similitud densa.

Sirve para intenciones de listado o conteo sobre el corpus indexado (TASK-70).
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models

from src.rag.runtime.filtros_listado_heuristica import especialidades_que_contienen

logger = logging.getLogger(__name__)

# Scroll sin filtro de payload: tope de lotes para no recorrer colecciones enormes en una sola tool-call.
_LISTADO_SIN_FILTRO_TAM_LOTE: int = 256
_LISTADO_SIN_FILTRO_MAX_LOTES: int = 32


class ItemListado(BaseModel):
    """Un elemento resumido para el compositor y la UI."""

    nombre: str = Field(description="Nombre del medico o titulo del recurso.")
    source_url: str = Field(default="", description="URL publica si existe en payload.")
    especialidad: list[str] = Field(default_factory=list)
    sedes: list[str] = Field(default_factory=list)
    archivo: str = Field(
        default="", description="Ruta relativa del Markdown de origen."
    )


class ResultadoListado(BaseModel):
    """Salida estable de :meth:`RecuperadorListados.listar`."""

    conteo: int = Field(
        ge=0, description="Total de elementos unicos tras deduplicar por URL/nombre."
    )
    items: list[ItemListado] = Field(default_factory=list)
    muestra_truncada: bool = Field(
        description="True si hay mas elementos unicos que la muestra devuelta (limite).",
    )
    filtros_aplicados: dict[str, Any] = Field(default_factory=dict)


def _construir_filtro(filtros: dict[str, Any]) -> models.Filter | None:
    """Arma ``models.Filter`` desde claves soportadas (AND entre must)."""
    must: list[models.Condition] = []
    tipo = filtros.get("tipo_pagina")
    if tipo and str(tipo).strip():
        must.append(
            models.FieldCondition(
                key="tipo_pagina",
                match=models.MatchValue(value=str(tipo).strip()),
            )
        )
    esp = filtros.get("especialidad")
    if esp and str(esp).strip():
        must.append(
            models.FieldCondition(
                key="especialidad",
                match=models.MatchValue(value=str(esp).strip()),
            )
        )
    esp_c = filtros.get("especialidad_contains")
    if esp_c and str(esp_c).strip():
        candidatos = especialidades_que_contienen(str(esp_c).strip())
        if candidatos:
            must.append(
                models.FieldCondition(
                    key="especialidad",
                    match=models.MatchAny(any=candidatos),
                )
            )
    sedes = filtros.get("sedes")
    if isinstance(sedes, list) and sedes:
        limpias = [str(s).strip() for s in sedes if str(s).strip()]
        if limpias:
            should = [
                models.FieldCondition(key="sedes", match=models.MatchValue(value=s))
                for s in limpias
            ]
            must.append(
                models.Filter(
                    min_should=models.MinShould(conditions=should, min_count=1),
                )
            )
    if not must:
        return None
    return models.Filter(must=must)


def _clave_dedupe(payload: dict[str, Any]) -> str:
    url = str(payload.get("source_url") or "").strip()
    if url:
        return f"url:{url}"
    nombre = str(payload.get("nombre_medico") or payload.get("titulo") or "").strip()
    archivo = str(payload.get("archivo") or "").strip()
    return f"nom:{nombre}|arch:{archivo}"


def _item_desde_payload(payload: dict[str, Any]) -> ItemListado:
    nombre = (
        str(payload.get("nombre_medico") or payload.get("titulo") or "").strip()
        or "(sin nombre)"
    )
    esp = payload.get("especialidad")
    espec_list: list[str] = [str(x) for x in esp] if isinstance(esp, list) else []
    sed = payload.get("sedes")
    sedes_list: list[str] = [str(x) for x in sed] if isinstance(sed, list) else []
    return ItemListado(
        nombre=nombre,
        source_url=str(payload.get("source_url") or ""),
        especialidad=espec_list,
        sedes=sedes_list,
        archivo=str(payload.get("archivo") or ""),
    )


class RecuperadorListados:
    """Scroll + filtro de payload sobre una coleccion Qdrant."""

    def __init__(self, cliente: QdrantClient, nombre_coleccion: str) -> None:
        self._cliente = cliente
        self._nombre_coleccion = nombre_coleccion

    def listar(
        self,
        filtros: dict[str, Any],
        *,
        limite: int = 50,
        offset_inicio: str | None = None,
    ) -> ResultadoListado:
        """
        Cuenta puntos unicos (dedupe) que cumplen ``filtros`` y devuelve hasta ``limite`` items.

        Args:
            filtros: Ver :func:`_construir_filtro` (``tipo_pagina``, ``especialidad``, ``sedes``, etc.).
            limite: Tamano maximo de ``items`` (la muestra).
            offset_inicio: Cursor de paginacion de ``client.scroll`` (opcional).
        """
        limite = max(1, min(int(limite), 500))
        filtro = _construir_filtro(filtros)
        filtros_aplicados = {
            k: v for k, v in filtros.items() if v not in (None, "", [], {})
        }
        vistos: dict[str, ItemListado] = {}
        offset = offset_inicio
        escaneo_completo = True
        lotes_sin_filtro = 0

        if filtro is None:
            logger.warning(
                "RecuperadorListados: sin filtro de payload; se usa scroll acotado (%s lotes x %s puntos).",
                _LISTADO_SIN_FILTRO_MAX_LOTES,
                _LISTADO_SIN_FILTRO_TAM_LOTE,
            )
            filtros_aplicados = {
                **filtros_aplicados,
                "sin_filtro_payload": True,
                "max_lotes_scroll": _LISTADO_SIN_FILTRO_MAX_LOTES,
            }

        while True:
            if filtro is None:
                if lotes_sin_filtro >= _LISTADO_SIN_FILTRO_MAX_LOTES:
                    escaneo_completo = False
                    break
                lotes_sin_filtro += 1
            puntos, siguiente = self._cliente.scroll(
                collection_name=self._nombre_coleccion,
                scroll_filter=filtro,
                limit=_LISTADO_SIN_FILTRO_TAM_LOTE,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            offset = siguiente
            for p in puntos:
                pl = p.payload if isinstance(p.payload, dict) else {}
                clave = _clave_dedupe(pl)
                if clave not in vistos:
                    vistos[clave] = _item_desde_payload(pl)
            if offset is None or not puntos:
                break

        items_ordenados = sorted(
            vistos.values(), key=lambda x: (x.nombre.lower(), x.archivo)
        )
        total = len(items_ordenados)
        muestra = items_ordenados[:limite]
        muestra_truncada = total > len(muestra) or not escaneo_completo
        return ResultadoListado(
            conteo=total,
            items=muestra,
            muestra_truncada=muestra_truncada,
            filtros_aplicados=filtros_aplicados,
        )
