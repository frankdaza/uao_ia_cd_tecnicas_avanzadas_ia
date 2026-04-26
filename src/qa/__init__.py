"""Componentes de preguntas y respuestas (clientes LLM, prompts, etc.)."""

from src.qa.cliente_ollama import (
    ClienteOllama,
    ConfiguracionLlm,
    ModeloNoDisponibleError,
    MODELOS_OLLAMA_SOPORTADOS,
    MODELO_GEMMA_4_E2B,
    MODELO_LLAMA_3_1_8B,
    OllamaNoAccesibleError,
)
from src.qa.pipeline import PipelineQa, RespuestaQa, construir_pipeline_por_defecto

__all__ = [
    "ClienteOllama",
    "ConfiguracionLlm",
    "ModeloNoDisponibleError",
    "MODELOS_OLLAMA_SOPORTADOS",
    "MODELO_GEMMA_4_E2B",
    "MODELO_LLAMA_3_1_8B",
    "OllamaNoAccesibleError",
    "PipelineQa",
    "RespuestaQa",
    "construir_pipeline_por_defecto",
]
