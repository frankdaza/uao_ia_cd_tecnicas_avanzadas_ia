"""
Tool LangChain para enumerar documentos indexados por payload (Qdrant scroll).
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.api.configuracion import Configuracion, obtener_configuracion
from src.rag.runtime.qdrant_store import obtener_qdrant_client
from src.rag.runtime.recuperador_listados import RecuperadorListados


class ArgsConsultaListados(BaseModel):
    """Argumentos para filtrar listados o conteos sobre el indice vectorial."""

    tipo_pagina: str | None = Field(
        default=None,
        description=(
            "Valor de payload ``tipo_pagina`` en Qdrant (p. ej. ``ficha_medico``, ``servicio``, "
            "``institucional``). Opcional si otros filtros bastan."
        ),
    )
    especialidad: str | None = Field(
        default=None,
        description="Coincidencia exacta contra un valor en el arreglo ``especialidad`` del payload.",
    )
    sedes: list[str] | None = Field(
        default=None,
        description="Lista de sedes; el documento debe contener al menos una (OR).",
    )
    especialidad_contains: str | None = Field(
        default=None,
        description="Subcadena para acotar especialidades canonicas (p. ej. ``oncolog``).",
    )
    limite: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Cantidad maxima de filas en ``items`` (el conteo total sigue siendo global).",
    )


def _filtros_desde_args(args: ArgsConsultaListados) -> dict[str, Any]:
    d: dict[str, Any] = {}
    if args.tipo_pagina and str(args.tipo_pagina).strip():
        d["tipo_pagina"] = str(args.tipo_pagina).strip()
    if args.especialidad and str(args.especialidad).strip():
        d["especialidad"] = str(args.especialidad).strip()
    if args.sedes:
        d["sedes"] = [str(s).strip() for s in args.sedes if str(s).strip()]
    if args.especialidad_contains and str(args.especialidad_contains).strip():
        d["especialidad_contains"] = str(args.especialidad_contains).strip()
    return d


def ejecutar_listar_estructurado_sync(
    *,
    tipo_pagina: str | None = None,
    especialidad: str | None = None,
    sedes: list[str] | None = None,
    especialidad_contains: str | None = None,
    limite: int = 50,
    configuracion: Configuracion | None = None,
) -> dict[str, Any]:
    """Ejecuta el listado con cliente y coleccion de settings (mismo camino que la tool)."""
    cfg = configuracion or obtener_configuracion()
    args = ArgsConsultaListados(
        tipo_pagina=tipo_pagina,
        especialidad=especialidad,
        sedes=sedes,
        especialidad_contains=especialidad_contains,
        limite=limite,
    )
    rec = RecuperadorListados(
        cliente=obtener_qdrant_client(cfg),
        nombre_coleccion=cfg.qdrant_collection,
    )
    salida = rec.listar(_filtros_desde_args(args), limite=int(limite))
    return salida.model_dump(mode="json")


def crear_listar_estructurado_tool(
    *,
    configuracion: Configuracion | None = None,
    recuperador: RecuperadorListados | None = None,
) -> StructuredTool:
    """
    Construye la ``StructuredTool`` ``listar_estructurado`` (scroll + filtro de payload).
    """
    cfg = configuracion or obtener_configuracion()
    rec_inyectado = recuperador

    def _ejecutar(
        tipo_pagina: str | None = None,
        especialidad: str | None = None,
        sedes: list[str] | None = None,
        especialidad_contains: str | None = None,
        limite: int = 50,
    ) -> dict[str, Any]:
        args = ArgsConsultaListados(
            tipo_pagina=tipo_pagina,
            especialidad=especialidad,
            sedes=sedes,
            especialidad_contains=especialidad_contains,
            limite=limite,
        )
        if rec_inyectado is not None:
            salida = rec_inyectado.listar(_filtros_desde_args(args), limite=args.limite)
            return salida.model_dump(mode="json")
        return ejecutar_listar_estructurado_sync(
            configuracion=cfg,
            tipo_pagina=args.tipo_pagina,
            especialidad=args.especialidad,
            sedes=args.sedes,
            especialidad_contains=args.especialidad_contains,
            limite=args.limite,
        )

    return StructuredTool.from_function(
        name="listar_estructurado",
        description=(
            "Enumera entidades del corpus institucional indexado en Qdrant filtrando por "
            "metadatos de payload (tipo de pagina, especialidad, sedes). Para un **catalogo de "
            "sedes** (ubicaciones institucionales) use ``tipo_pagina=\"sede\"`` solo; no pase "
            "todas las sedes conocidas en el argumento ``sedes`` para significar \"todas las "
            "sedes\" (eso hace OR sobre menciones en cualquier pagina, p. ej. notas). Usar cuando "
            "la consulta pida listar, enumerar o contar conjuntos (p. ej. pediatras por sede) "
            "donde la busqueda semantica top-k no basta. No sustituye a ``rag_denso`` para "
            "preguntas abiertas de texto ni a FAQ determinista."
        ),
        func=_ejecutar,
        args_schema=ArgsConsultaListados,
        infer_schema=False,
    )
