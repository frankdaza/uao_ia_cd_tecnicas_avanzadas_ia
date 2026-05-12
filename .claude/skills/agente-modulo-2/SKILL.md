---
name: agente-modulo-2
description: Agente conversacional M2 con LangGraph (router), LangChain (tools, memoria Postgres), LlamaIndex + Qdrant (RAG denso), SQLAlchemy async y SSE extendido. Usar al implementar o revisar src/agentes/, src/rag/, src/persistencia/, scripts de ingesta Qdrant o endpoints de sesion/agente.
---

# Agente conversacional — Modulo 2

> Mantener el mismo contenido en `.cursor/skills/agente-modulo-2/` y `.claude/skills/agente-modulo-2/`.

## Cuando usar esta skill

- Codigo bajo **`src/agentes/`** (router LangGraph, estado, meta-prompt, herramientas).
- Codigo bajo **`src/rag/`** (embeddings, Qdrant, chunking para vectores, recuperador denso).
- Codigo bajo **`src/persistencia/`** (motor SQLAlchemy async, modelos Alembic, repositorios).
- Script **`scripts/indexar_corpus_qdrant.py`** (ingesta idempotente desde `data/markdown/`).
- Integracion con API: **`src/api/routers/agente.py`**, **`src/api/routers/sesiones.py`** y esquemas SSE del agente.

## Decision de arquitectura (resumen)

- **ADR**: ver `backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md` cuando exista en el repo (router + memoria + RAG denso).
- **Guia operativa**: `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` (task-62) cuando exista.
- **M1 vs M2**: el Modulo 1 uso BM25 sobre `data/markdown/` en runtime; el **M2** usa **solo recuperacion densa en Qdrant** en el producto (sin fusion hibrida con BM25). `data/markdown/` sigue siendo fuente para **ingesta**, no para lectura en cada pregunta del agente.

## Stack permitido (M2)

| Capa | Paquetes / servicios |
| --- | --- |
| Router | `langgraph`, `langchain-core` |
| LLM / tools | `langchain-openai`, `StructuredTool`, tool binding |
| Memoria | `langchain-postgres` (`PostgresChatMessageHistory`), tabla `chat_history` |
| App DB | `sqlalchemy[asyncio]`, `asyncpg`, `alembic` (tabla `usuarios`, etc.) |
| Driver sync LC | `psycopg[binary]` para rutas que exijan conexion sync documentada |
| RAG | `llama-index-core`, `llama-index-vector-stores-qdrant`, `llama-index-embeddings-openai` (y opcional HuggingFace embeddings) |
| Vector DB | `qdrant-client`, Qdrant en Docker |
| API | FastAPI + `sse-starlette` (SSE multi-evento) |

## Convenciones del repo

- **Identificadores Python**: espanol **ASCII** (regla `language-conventions.mdc`).
- **Excepcion controlada**: el campo `name` de herramientas LangChain/OpenAI suele ir en **ingles estable** (p. ej. `faq_estructurada`, `rag_denso`) para contratos de tool-calling; documentar en descripcion de la tool en espanol.
- **Secretos**: solo `.env` local; nunca API keys en `config/router_meta_prompt.json`, `data/structured/faqs.json` ni `backlog/tasks/`.

## LangGraph (router)

- Modelar estado con **`TypedDict`** o esquema recomendado por la version de LangGraph; campos tipicos: pregunta, mensajes de contexto, tool elegida, resultado de tool, respuesta final, fuentes, pensamientos, usuario, `session_id`, `primer_turno`.
- **Nodos** claros: cargar memoria → decidir tool (LLM con bind_tools) → ejecutar tool → componer respuesta → persistir turno.
- **Edges condicionales** segun `tool_calls` del router; evitar logica duplicada entre nodos.
- **Streaming**: preferir `astream_events` (o API estable de la version pinneada) y mapear eventos a SSE en la capa FastAPI (ver skill `fastapi-sse-api`).

## LangChain (tools y memoria)

- **Tools**: `StructuredTool` con entrada/salida tipada (Pydantic); FAQ **determinista** sin LLM interno ni Qdrant.
- **Memoria**: `session_id` estable por usuario (p. ej. `user:{uuid}`); respetar `HISTORIAL_DIAS_MAX` y `HISTORIAL_TURNOS_MAX` desde settings.
- **Sync vs async**: SQLAlchemy **async** para dominio app; si LangChain Postgres exige sync, aislar en helper o executor y **no** bloquear el event loop largo (p. ej. `asyncio.to_thread` para tramos acotados, o diseno documentado).

## LlamaIndex + Qdrant (RAG denso)

- **Ingesta**: chunking con `SentenceSplitter` (parametros desde `.env`); ids de punto **idempotentes** (hash de ruta + indice + texto o esquema equivalente).
- **Payload**: metadatos minimos (`archivo`, `titulo`, `source_url`, `chunk_index`, hashes utiles) para trazabilidad en UI.
- **Consulta**: embedding de la pregunta + top-k + umbral de score; sin BM25 en el camino productivo.
- **Tests**: `QdrantClient(location=":memory:")` o contenedor; **mockear embeddings** en CI cuando no haya API key.

## Meta-prompt y datos estructurados

- **`config/router_meta_prompt.json`**: versionado; validar con Pydantic al cargar; recarga por `mtime` si se implementa caché.
- **`data/structured/faqs.json`**: validar contra JSON Schema; contenido institucional publico solamente.

## Pruebas recomendadas

- Router: `FakeListChatModel` (LangChain) para secuencias deterministas de tool_calls y texto.
- Markers pytest: `integration_postgres`, `integration_qdrant` con skip claro si no hay servicios.
- API: `httpx.AsyncClient` + `ASGITransport`; SSE leido como stream de lineas.

## Documentacion externa (referencia)

- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangChain](https://python.langchain.com/docs/)
- [LlamaIndex](https://docs.llamaindex.ai/)
- [Qdrant](https://qdrant.tech/documentation/)

Las APIs cambian entre versiones; ceñirse a las versiones declaradas en `pyproject.toml` / `uv.lock` del repo.

## Regla Cursor asociada

- Convenciones y checklist en `.cursor/rules/agente-modulo-2.mdc` (globs acotados).
