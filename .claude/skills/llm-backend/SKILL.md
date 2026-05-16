---
name: llm-backend
description: LLM en el repo (clientes Ollama/OpenAI en src/laboratorio/qa_legacy, agente M2 LangGraph LangChain LlamaIndex Qdrant). Usar al disenar src/laboratorio/qa_legacy src/agentes src/rag o integracion con modelos.
---

# Backend LLM

> Mantener el mismo contenido en `.cursor/skills/llm-backend/` y `.claude/skills/llm-backend/`.

## Modulo 1 (BM25 / PipelineQa)

El pipeline BM25 + `PipelineQa` **se retiro del arbol de codigo**. El contexto historico vive en ADRs (`decision-1`, `decision-2`, `decision-3`) y en commits anteriores.

## Modulo 2 (agente conversacional)

- **Stack combinado**: **LangGraph** (router), **LangChain** (StructuredTool, memoria con `langchain-postgres`), **LlamaIndex** (RAG denso sobre **Qdrant**), **OpenAI** (u otro proveedor) segun configuracion.
- **Detalle de implementacion**, pruebas con fakes, ingesta e idempotencia: skill **`agente-modulo-2`**.
- **ADR**: `backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md`.

## Clientes y prompts en `src/laboratorio/qa_legacy/`

- **Ollama** y **OpenAI**: modulos `cliente_ollama.py`, `cliente_openai.py`; variables `OLLAMA_BASE_URL`, `OPENAI_API_KEY`, modelos en `.env.example`.
- **Prompt**: `prompt.py` con `PROMPT_SISTEMA_DEFECTO`, `componer_mensajes` / `componer_mensajes_multi` usando `DocumentoContexto` (sin acoplamiento a recuperadores retirados).

Ver skill `fastapi-sse-api` para patrones SSE del agente y tests.
