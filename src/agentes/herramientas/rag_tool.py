"""
Tool de recuperacion densa (Qdrant + LlamaIndex) para el router del agente M2.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

from src.api.configuracion import Configuracion, obtener_configuracion
from src.rag.runtime.recuperador_denso import RecuperadorDenso, SalidaRecuperacionRagDenso


class ArgsConsultaRagDenso(BaseModel):
    """Entrada de la tool: consulta del modelo mas parametros RAG inyectados por el router."""

    model_config = ConfigDict(extra="ignore")

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
    top_k: int | None = Field(
        default=None,
        description="Interno: el servidor completa desde RuntimeAgenteBundle.",
    )
    score_minimo: float | None = Field(
        default=None,
        description="Interno: el servidor completa desde RuntimeAgenteBundle.",
    )
    top_k_inicial: int | None = Field(
        default=None,
        description="Interno: el servidor completa desde RuntimeAgenteBundle.",
    )
    mmr_habilitado: bool | None = Field(
        default=None,
        description="Interno: el servidor completa desde RuntimeAgenteBundle.",
    )
    mmr_lambda: float | None = Field(
        default=None,
        description="Interno: el servidor completa desde RuntimeAgenteBundle.",
    )
    reranker_habilitado: bool | None = Field(
        default=None,
        description="Interno: el servidor completa desde RuntimeAgenteBundle.",
    )
    reranker_modelo: str | None = Field(
        default=None,
        description="Interno: el servidor completa desde RuntimeAgenteBundle.",
    )
    reranker_top_n_entrada: int | None = Field(
        default=None,
        description="Interno: el servidor completa desde RuntimeAgenteBundle.",
    )
    reranker_batch_size: int | None = Field(
        default=None,
        description="Interno: el servidor completa desde RuntimeAgenteBundle.",
    )


def ejecutar_rag_denso_sync(
    *,
    consulta: str,
    top_k: int,
    score_minimo: float,
    configuracion: Configuracion | None = None,
    filtros_tipo_pagina: list[str] | None = None,
    top_k_inicial: int | None = None,
    mmr_habilitado: bool | None = None,
    mmr_lambda: float | None = None,
    reranker_habilitado: bool | None = None,
    reranker_modelo: str | None = None,
    reranker_top_n_entrada: int | None = None,
    reranker_batch_size: int | None = None,
) -> dict[str, Any]:
    """
    Ejecuta la recuperacion densa con umbrales explicitos (p. ej. desde RuntimeAgenteBundle).

    Usa el mismo pipeline que la tool ``rag_denso`` para mantener un solo camino de serializacion.
    Los parametros opcionales MMR/reranker (``None``) se toman de ``configuracion`` / ``.env``.
    """
    cfg = configuracion or obtener_configuracion()
    rec = RecuperadorDenso.desde_configuracion(
        cfg,
        top_k=top_k,
        score_minimo=score_minimo,
        top_k_inicial=top_k_inicial,
        mmr_habilitado=mmr_habilitado,
        mmr_lambda=mmr_lambda,
        reranker_habilitado=reranker_habilitado,
        reranker_modelo=reranker_modelo,
        reranker_top_n_entrada=reranker_top_n_entrada,
        reranker_batch_size=reranker_batch_size,
    )
    salida: SalidaRecuperacionRagDenso = rec.consultar(
        consulta,
        filtros_tipo_pagina=filtros_tipo_pagina,
    )
    return salida.model_dump(mode="json")


def crear_rag_tool(
    *,
    configuracion_motor: Configuracion | None = None,
    recuperador: RecuperadorDenso | None = None,
) -> StructuredTool:
    """
    Construye la ``StructuredTool`` ``rag_denso`` (binding con LangGraph / tool-calling).

    Los umbrales RAG no se leen de ``configuracion_motor`` en cada invocacion: deben llegar
    explicitamente en los argumentos (el router los toma de :class:`~src.agentes.runtime_agente.RuntimeAgenteBundle`).
    ``configuracion_motor`` solo orienta URLs/claves de Qdrant y embeddings al construir el recuperador.

    En pruebas puede inyectarse un ``RecuperadorDenso`` ya configurado (solo se usa ``consulta`` / filtros).
    """
    rec_inyectado = recuperador

    def _ejecutar(
        consulta: str,
        filtros_tipo_pagina: list[str] | None = None,
        top_k: int | None = None,
        score_minimo: float | None = None,
        top_k_inicial: int | None = None,
        mmr_habilitado: bool | None = None,
        mmr_lambda: float | None = None,
        reranker_habilitado: bool | None = None,
        reranker_modelo: str | None = None,
        reranker_top_n_entrada: int | None = None,
        reranker_batch_size: int | None = None,
    ) -> dict[str, Any]:
        if rec_inyectado is not None:
            salida: SalidaRecuperacionRagDenso = rec_inyectado.consultar(
                consulta,
                filtros_tipo_pagina=filtros_tipo_pagina,
            )
            return salida.model_dump(mode="json")
        faltan = [
            nombre
            for nombre, val in (
                ("top_k", top_k),
                ("score_minimo", score_minimo),
                ("top_k_inicial", top_k_inicial),
                ("mmr_habilitado", mmr_habilitado),
                ("mmr_lambda", mmr_lambda),
                ("reranker_habilitado", reranker_habilitado),
                ("reranker_modelo", reranker_modelo),
                ("reranker_top_n_entrada", reranker_top_n_entrada),
                ("reranker_batch_size", reranker_batch_size),
            )
            if val is None
        ]
        if faltan:
            msg = (
                "rag_denso requiere parametros RAG explicitos en cada invocacion "
                f"(faltan: {', '.join(faltan)})."
            )
            raise ValueError(msg)
        cfg_motor = configuracion_motor or obtener_configuracion()
        return ejecutar_rag_denso_sync(
            configuracion=cfg_motor,
            consulta=consulta,
            top_k=int(top_k),
            score_minimo=float(score_minimo),
            filtros_tipo_pagina=filtros_tipo_pagina,
            top_k_inicial=int(top_k_inicial),
            mmr_habilitado=bool(mmr_habilitado),
            mmr_lambda=float(mmr_lambda),
            reranker_habilitado=bool(reranker_habilitado),
            reranker_modelo=str(reranker_modelo).strip(),
            reranker_top_n_entrada=int(reranker_top_n_entrada),
            reranker_batch_size=int(reranker_batch_size),
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

