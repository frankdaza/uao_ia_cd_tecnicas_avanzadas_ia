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
    """

    llm_router: Any
    llm_compositor: BaseChatModel
    meta_prompt: MetaPromptConfig
    prompt_institucional: str
    etiqueta_modelo_compositor: str


__all__ = ["RuntimeAgenteBundle"]
