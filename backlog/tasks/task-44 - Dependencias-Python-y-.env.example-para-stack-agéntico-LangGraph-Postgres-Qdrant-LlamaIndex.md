---
id: TASK-44
title: >-
  Dependencias Python y .env.example para stack agéntico (LangGraph, Postgres,
  Qdrant, LlamaIndex)
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-12 05:53'
labels:
  - uv
  - backend
  - configuracion
  - modulo-2
dependencies:
  - TASK-43
references:
  - pyproject.toml
  - uv.lock
  - .env.example
  - src/api/configuracion.py
documentation:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
  - .claude/skills/uv-python-env/SKILL.md
priority: high
ordinal: 0.0625
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La arquitectura M2 añade orquestación con **LangGraph**, memoria con **langchain-postgres**, RAG denso con **LlamaIndex + Qdrant**, acceso async a PostgreSQL con **SQLAlchemy 2 async + asyncpg**, driver **psycopg** para rutas síncronas de LangChain, y **alembic** para migraciones. El runtime **ya no** debe depender de BM25: hay que **eliminar** del manifiesto `rank-bm25`, `nltk` y `numpy` si ningún otro módulo los requiere (verificar con `rg` en el repo antes de quitar).

## Objetivo

1. Añadir dependencias con `uv add`: `langchain-core`, `langgraph`, `langchain-postgres`, `langchain-openai`, `llama-index-core`, `llama-index-vector-stores-qdrant`, `llama-index-embeddings-openai`, `qdrant-client`, `sqlalchemy[asyncio]`, `asyncpg`, `psycopg[binary]`, `alembic` (y subpaquetes LlamaIndex opcionales para HuggingFace embeddings si se documentan en ADR).
2. Extender **`.env.example`** (sin secretos) con bloques documentados:
   - **PostgreSQL**: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL` (async).
   - **Qdrant**: `QDRANT_URL`, `QDRANT_API_KEY` (opcional), `QDRANT_COLLECTION`, `QDRANT_DISTANCE=Cosine`.
   - **Embeddings**: `EMBEDDING_PROVIDER=openai|huggingface`, `EMBEDDING_MODEL=text-embedding-3-small`, `EMBEDDING_DIMS=1536`.
   - **Chunking**: `CHUNK_SIZE=512`, `CHUNK_OVERLAP=80`, `CHUNK_STRATEGY=sentence`.
   - **RAG**: `RAG_TOP_K=5`, `RAG_SCORE_MINIMO=0.25`.
   - **Memoria**: `HISTORIAL_DIAS_MAX=7`, `HISTORIAL_TURNOS_MAX=20`.
   - **FAQ**: `FAQ_UMBRAL_MATCH=0.5`.
   - **Router**: `ROUTER_META_PROMPT_PATH=config/router_meta_prompt.json`, `ROUTER_LLM_MODEL=gpt-4o-mini`.
3. Preparar extensión de `src/api/configuracion.py` (Pydantic Settings) para leer las nuevas variables (implementación completa puede repartirse con tasks posteriores, pero los nombres deben estar acordados aquí).

## Alcance explícito

- **Quitar** dependencias BM25 del `pyproject.toml` cuando el código legacy BM25 salga del árbol productivo (coordinar con task-57 si hay orden estricto; esta task puede dejar el grep y la eliminación como checklist si aún hay imports vivos).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [x] #1 `uv add` ejecutado; `pyproject.toml` y `uv.lock` versionados con todas las dependencias agénticas listadas
- [x] #2 `rank-bm25`, `nltk` y `numpy` eliminados **o** justificados en notas si aún queda código legacy hasta task-57 (documentar estado intermedio)
- [x] #3 `.env.example` incluye todos los bloques de variables con comentarios en español latinoamericano
- [x] #4 `DATABASE_URL` documentado para SQLAlchemy async (postgresql+asyncpg://…)
- [x] #5 `uv sync` + `uv run python -c "import langgraph, llama_index"` smoke sin error
- [x] #6 Ningún secreto ni API key en `.env.example`
- [x] #7 Lista de paquetes alineada con decision-3 (sin dependencias BM25 en estado final del M2)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. `rg` en el repo por `rank_bm25`, `nltk`, `numpy` y listar archivos dependientes.
2. `uv add` paquetes agénticos en lote razonable; resolver conflictos de versiones.
3. Editar `.env.example` con bloques agrupados y valores placeholder seguros.
4. Añadir campos a `ConfiguracionApi` / settings con defaults sensatos y validación.
5. `uv lock` y `uv run ruff check` en archivos tocados.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- HuggingFace: si se usa `llama-index-embeddings-huggingface`, añadirlo explícitamente y documentar tamaño de descarga en README (task-63).
- Mantener compatibilidad con variables existentes del Módulo 1 (OpenAI, CORS) sin romper arranque local.
- **BM25 (estado intermedio):** `rank-bm25`, `nltk` y `numpy` siguen en `pyproject.toml` porque `src/retrieval/recuperador.py` los importa para el camino M1; retirarlos queda coordinado con task-57 cuando el legacy BM25 salga del árbol productivo.

BM25: rank-bm25, nltk y numpy permanecen mientras src/retrieval/recuperador.py sea el camino M1; retiro alineado a task-57.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se anadieron dependencias agénticas con uv (langgraph, langchain-*, llama-index-*, qdrant-client, sqlalchemy[asyncio], asyncpg, psycopg[binary], alembic). Se amplio src/api/configuracion.py con variables M2 y metodo url_base_datos_async(). Se actualizo .env.example con bloques PostgreSQL, Qdrant, embeddings, chunking, RAG, memoria, FAQ y router. rank-bm25/nltk/numpy se conservan por codigo BM25 activo hasta task-57. pytest 125 ok, ruff ok, smoke import langgraph+llama_index ok.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest` pasa en el estado del repo tras cambios (o skips documentados si aún hay BM25 hasta task-57)
- [x] #2 `ruff check` sin errores nuevos en archivos Python modificados
- [x] #3 `uv.lock` actualizado y commiteado
- [x] #4 Revisión: ninguna clave real en `.env.example`
<!-- DOD:END -->
