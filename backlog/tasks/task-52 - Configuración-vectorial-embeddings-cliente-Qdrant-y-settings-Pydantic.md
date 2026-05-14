---
id: TASK-52
title: 'Configuración vectorial: embeddings, cliente Qdrant y settings Pydantic'
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-14 19:32'
labels:
  - qdrant
  - embeddings
  - llama-index
  - modulo-2
dependencies:
  - TASK-44
references:
  - src/rag/embeddings.py
  - src/rag/qdrant_store.py
  - src/api/configuracion.py
documentation:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
  - .claude/skills/llm-backend/SKILL.md
priority: high
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El RAG denso requiere una fábrica de **embeddings** compatible con LlamaIndex y un **cliente Qdrant** reutilizable, con colección y métrica de distancia configurables por entorno.

## Objetivo

1. **`src/rag/embeddings.py`**: función `obtener_embeddings()` que retorna:
   - `OpenAIEmbedding(model=EMBEDDING_MODEL)` cuando `EMBEDDING_PROVIDER=openai`.
   - `HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)` cuando `=huggingface` (dependencia opcional añadida en task-44 si aplica).

2. **`src/rag/qdrant_store.py`**:
   - `obtener_qdrant_client()` lazy/singleton thread-safe a nivel proceso.
   - `asegurar_coleccion(nombre, dims, distancia)` idempotente (crea si no existe; valida dims vs settings).
   - `obtener_vector_store() -> QdrantVectorStore` listo para ingestión y query LlamaIndex.

3. Extender **`src/api/configuracion.py`** con todas las variables del bloque vectorial ya listadas en task-44, más validaciones (p. ej. `EMBEDDING_DIMS` coherente con modelo OpenAI small = 1536).

## Observabilidad

Logs de inicio: proveedor de embeddings, nombre de colección, **sin** API keys.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `obtener_embeddings()` selecciona proveedor según env sin errores de import circular
- [x] #2 Cliente Qdrant reusable; tests pueden inyectar `location=":memory:"` vía env o fixture
- [x] #3 `asegurar_coleccion` no falla si la colección ya existe con mismos parámetros; falla explícito si dims mismatch
- [x] #4 Settings validan enums (`Cosine`, `Dot`, etc.) contra valores soportados por Qdrant
- [x] #5 Documentación inline de variables en español latinoamericano
- [x] #6 Smoke: instanciar embeddings con API key falsa debe fallar solo al embed real (no al import)
- [x] #7 Tests unitarios mínimos de factory con mocks
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Añadir settings con `Field` y `model_validator` donde aplique.
2. Implementar factories en `src/rag/`.
3. Añadir tests con Qdrant in-memory o mock client.
4. Exponer helpers para scripts (task-53) y RagTool (task-54).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Alinear nombres de distancia LlamaIndex ↔ Qdrant (`COSINE` vs `Cosine`).
- Para HuggingFace, documentar RAM/GPU requerida en doc-003.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se anadieron `src/rag/embeddings.py` (OpenAI con `dimensions` solo en modelos text-embedding-3*, HuggingFace con import diferido), `src/rag/qdrant_store.py` (cliente singleton thread-safe, `QDRANT_URL=:memory:`, `asegurar_coleccion`, `obtener_vector_store`), extension de `Configuracion` con `TipoDistanciaQdrant`, `Field` documentados y validacion de dims para `text-embedding-ada-002`, y log de modulo vectorial en `lifespan`. Tests en `tests/rag/`. Dependencia `llama-index-embeddings-huggingface` en `pyproject.toml` (torch como transitorio).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest` verde para tests nuevos bajo `tests/rag/`
- [x] #2 `ruff check` sin errores nuevos
- [x] #3 `uv.lock` ya incluye dependencias de task-44
<!-- DOD:END -->
