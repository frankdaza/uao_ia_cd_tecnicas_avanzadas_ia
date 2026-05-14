"""
Tool de recuperacion densa (Qdrant + LlamaIndex) para el router del agente M2.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.api.configuracion import Configuracion, obtener_configuracion
from src.rag.embeddings import obtener_embeddings
from src.rag.qdrant_store import obtener_vector_store
from src.rag.recuperador_denso import RecuperadorDenso, SalidaRecuperacionRagDenso


class ArgsConsultaRagDenso(BaseModel):
    """Entrada expuesta al modelo para recuperar contexto del corpus vectorizado."""

    consulta: str = Field(
        description=(
            "Pregunta o consulta en español sobre politicas, servicios, historia, "
            "investigacion o documentacion amplia de la Fundacion Valle del Lili (FVL), "
            "que requiera contexto profundo del corpus institucional indexado."
        ),
        min_length=1,
    )
    filtros_tipo_pagina: list[str] | None = Field(
        default=None,
        description=(
            "Opcional: acota la busqueda densa a estos valores de ``tipo_pagina`` en el payload "
            "(p. ej. ``institucional`` para mision/vision). Lista vacia se ignora."
        ),
    )


def ejecutar_rag_denso_sync(
    *,
    consulta: str,
    top_k: int,
    score_minimo: float,
    configuracion: Configuracion | None = None,
    filtros_tipo_pagina: list[str] | None = None,
) -> dict[str, Any]:
    """
    Ejecuta la recuperacion densa con umbrales explicitos (p. ej. desde RuntimeAgenteBundle).

    Usa el mismo pipeline que la tool ``rag_denso`` para mantener un solo camino de serializacion.
    """
    cfg = configuracion or obtener_configuracion()
    rec = RecuperadorDenso(
        vector_store=obtener_vector_store(cfg),
        embeddings=obtener_embeddings(cfg),
        top_k=top_k,
        score_minimo=score_minimo,
    )
    salida: SalidaRecuperacionRagDenso = rec.consultar(
        consulta,
        filtros_tipo_pagina=filtros_tipo_pagina,
    )
    return salida.model_dump(mode="json")


def crear_rag_tool(
    *,
    configuracion: Configuracion | None = None,
    recuperador: RecuperadorDenso | None = None,
) -> StructuredTool:
    """
    Construye la ``StructuredTool`` ``rag_denso`` (binding con LangGraph / tool-calling).

    Por defecto usa ``obtener_vector_store``, ``obtener_embeddings`` y los umbrales
    ``RAG_TOP_K`` / ``RAG_SCORE_MINIMO`` de settings. En pruebas puede inyectarse un
    ``RecuperadorDenso`` ya configurado.
    """
    cfg = configuracion or obtener_configuracion()
    rec_inyectado = recuperador

    def _ejecutar(
        consulta: str,
        filtros_tipo_pagina: list[str] | None = None,
    ) -> dict[str, Any]:
        if rec_inyectado is not None:
            salida: SalidaRecuperacionRagDenso = rec_inyectado.consultar(
                consulta,
                filtros_tipo_pagina=filtros_tipo_pagina,
            )
            return salida.model_dump(mode="json")
        return ejecutar_rag_denso_sync(
            configuracion=cfg,
            consulta=consulta,
            top_k=cfg.rag_top_k,
            score_minimo=cfg.rag_score_minimo,
            filtros_tipo_pagina=filtros_tipo_pagina,
        )

    return StructuredTool.from_function(
        name="rag_denso",
        description=(
            "Recupera fragmentos relevantes del corpus institucional de la Fundación "
            "Valle del Lili mediante búsqueda semántica densa en Qdrant (embeddings). "
            "Úsala para preguntas abiertas de dominio FVL que requieran contexto textual "
            "profundo (normativas, descripciones extensas, contenido web convertido a "
            "Markdown indexado). No sustituye datos FAQ puntuales ni razonamiento clínico; "
            "si no hay fragmentos por encima del umbral de similitud, el compositor debe "
            "responder que no hay información suficiente."
        ),
        func=_ejecutar,
        args_schema=ArgsConsultaRagDenso,
        infer_schema=False,
    )
