"""Componentes de preguntas y respuestas (clientes LLM, prompts, etc.)."""

from __future__ import annotations

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
from src.qa.documento_contexto import DocumentoContexto

__all__ = [
    "ClienteOllama",
    "ConfiguracionLlm",
    "DocumentoContexto",
    "ModeloNoDisponibleError",
    "MODELOS_OLLAMA_SOPORTADOS",
    "MODELO_GEMMA_4_E2B",
    "MODELO_GEMMA_4_E4B",
    "MODELO_LLAMA_3_1_8B",
    "OllamaNoAccesibleError",
]
