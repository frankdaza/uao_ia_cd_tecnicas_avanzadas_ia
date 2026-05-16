"""Utilidades de preguntas y respuestas fuera del runtime productivo M2.

Este paquete agrupa clientes LLM (por ejemplo Ollama), composición de mensajes
y piezas reutilizables para **laboratorio**, material del **Módulo 1** del curso
y **pruebas** que importan estos módulos. **No** forma parte del runtime M2 en
producción: el endpoint ``POST /api/agente/stream`` y el grafo LangGraph **no**
dependen de ``src/qa``.

Para el agente conversacional productivo (router, tools, memoria Postgres,
RAG en Qdrant), usar ``src/agentes/`` y la guía
`backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md`.
"""

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
