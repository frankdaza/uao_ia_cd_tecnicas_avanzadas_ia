---
name: llm-backend
description: LLM en el repo Modulos 1 y 2 M1 PipelineQa BM25 OpenAI Ollama M2 LangGraph LangChain LlamaIndex Qdrant. Usar al disenar src/qa src/agentes src/rag o integracion con modelos.
---

# Backend LLM

> Mantener el mismo contenido en `.cursor/skills/llm-backend/` y `.claude/skills/llm-backend/`.

## Modulo 1 (Q&A legacy)

### Eleccion de modelo

- **Ollama**: modelo open source local; sin costo por token; requiere Ollama instalado y modelo descargado.
- **OpenAI (u otro API)**: requiere clave en `.env`; no commitear secretos.

### Framework (M1)

- Elegir **uno**: LangChain **o** LlamaIndex para la cadena simple del MVP; envolver la llamada al modelo en funciones con interfaces claras (`generar_respuesta`, `invocar_modelo`).

### Configuracion

- Variables como `OLLAMA_BASE_URL`, `OPENAI_API_KEY`, `MODELO_LLM` en `.env.example` sin valores reales.
- Cargar con `pydantic-settings` o equivalente si el proyecto lo define.

### Identificadores

- Modulos y funciones en espanol ASCII; nombres de clases descriptivos (`ClienteLlm`, `ConfiguracionModelo`).

### Exposicion via HTTP y SSE (M1)

El `PipelineQa` de `src/qa/pipeline.py` (mientras exista) expone capacidades via `src/api/routers/qa.py`. Metodos tipicos del diseno historico:

- `responder`, `responder_stream`, `responder_openai_stream`, `preparar_contexto_inferencia` (BM25), streams dual si aun estan registrados.

**Nota historica**: el modo dual y BM25 pueden retirarse al cerrar el M2; no tomar este bloque como fuente de verdad del producto final si el ADR `decision-3` ya declaro solo Qdrant en runtime.

Ver skill `fastapi-sse-api` para patrones SSE y tests.

## Modulo 2 (agente conversacional)

- **Stack combinado**: **LangGraph** (router), **LangChain** (StructuredTool, memoria con `langchain-postgres`), **LlamaIndex** (RAG denso sobre **Qdrant**), **OpenAI** (u otro proveedor) segun configuracion.
- **Detalle de implementacion**, pruebas con fakes, ingesta e idempotencia: skill **`agente-modulo-2`**.
- **ADR** (cuando exista en el repo): `backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md`.
