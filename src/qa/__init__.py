"""Componentes de preguntas y respuestas (clientes LLM, prompts, etc.)."""

from __future__ import annotations

from typing import Any

from src.qa.cliente_ollama import (
    ClienteOllama,
    ConfiguracionLlm,
    ModeloNoDisponibleError,
    MODELOS_OLLAMA_SOPORTADOS,
    MODELO_GEMMA_4_E2B,
    MODELO_GEMMA_4_E4B,
    MODELO_LLAMA_3_1_8B,
    OllamaNoAccesibleError,
)

__all__ = [
    "FuenteBm25",
    "ClienteOllama",
    "ConfiguracionLlm",
    "ModeloNoDisponibleError",
    "MODELOS_OLLAMA_SOPORTADOS",
    "MODELO_GEMMA_4_E2B",
    "MODELO_GEMMA_4_E4B",
    "MODELO_LLAMA_3_1_8B",
    "OllamaNoAccesibleError",
    "PipelineQa",
    "RespuestaQa",
    "construir_pipeline_por_defecto",
]


def __getattr__(name: str) -> Any:
    """Carga diferida de ``pipeline`` para no importar BM25 al cargar submodulos como ``prompt``."""
    if name in ("PipelineQa", "RespuestaQa", "FuenteBm25", "construir_pipeline_por_defecto"):
        from src.qa import pipeline as _pipeline

        return getattr(_pipeline, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
