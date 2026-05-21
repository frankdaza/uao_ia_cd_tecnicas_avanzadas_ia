"""Snapshot de dependencias del agente M2 resueltas por peticion (runtime / hot-reload)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from src.agentes.meta_prompt import MetaPromptConfig


@dataclass(frozen=True, slots=True)
class RuntimeAgenteBundle:
    """
    Conjunto inmutable de LLMs y textos usados por el grafo en una invocacion.

    Se pasa por ``RunnableConfig['configurable']['runtime_agente']`` para que los
    nodos tomen valores actualizados sin recompilar el grafo compilado al boot.
    ``historial_dias_max`` y ``historial_turnos_max`` acotan la ventana temporal y la
    cantidad de turnos humanos cargados desde Postgres para router y compositor.

    Los campos ``rag_*`` adicionales alinean la tool ``rag_denso`` con overrides admin
    o valores de :class:`~src.api.configuracion.Configuracion`.
    """

    llm_router: Any
    llm_compositor: BaseChatModel
    meta_prompt: MetaPromptConfig
    prompt_institucional: str
    etiqueta_modelo_compositor: str
    rag_top_k: int = 5
    rag_score_minimo: float = 0.25
    historial_turnos_max: int = 20
    historial_dias_max: int = 7
    rag_top_k_inicial: int = 20
    rag_mmr_habilitado: bool = True
    rag_mmr_lambda: float = 0.5
    rag_reranker_habilitado: bool = False
    rag_reranker_modelo: str = "BAAI/bge-reranker-base"
    rag_reranker_top_n_entrada: int = 10
    rag_reranker_batch_size: int = 16


__all__ = ["RuntimeAgenteBundle"]
