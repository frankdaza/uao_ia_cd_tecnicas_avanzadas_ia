---
id: TASK-54
title: RagTool denso (Qdrant vía LlamaIndex) y RecuperadorDenso
status: In Progress
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-12 07:08'
labels:
  - rag
  - qdrant
  - llama-index
  - modulo-2
dependencies:
  - TASK-52
  - TASK-53
references:
  - src/rag/recuperador_denso.py
  - src/agentes/herramientas/rag_tool.py
  - tests/rag/test_recuperador_denso.py
documentation:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El router debe invocar una tool de RAG que consulte **únicamente Qdrant** con búsqueda por similitud densa (embeddings de la pregunta), filtrando por score mínimo configurable.

## Objetivo

1. **`src/rag/recuperador_denso.py`**: clase `RecuperadorDenso(vector_store, embeddings, top_k, score_minimo)` con método principal que:
   - Embedea la consulta.
   - Ejecuta query contra `QdrantVectorStore` / cliente (API LlamaIndex) recuperando `top_k` resultados.
   - Filtra por `score >= RAG_SCORE_MINIMO` (settings).
   - Devuelve lista de chunks ordenada por score descendente.

2. **`src/agentes/herramientas/rag_tool.py`**: `crear_rag_tool() -> StructuredTool` con:
   - `name="rag_denso"`
   - Descripción orientada al router (preguntas abiertas de dominio FVL, contexto profundo del corpus).

3. **Salida estructurada** hacia el LLM compositor:
   - `respuesta_contexto`: string concatenando chunks con cabecera tipo `[CHUNK i] titulo / URL`
   - `fuentes`: lista `{ archivo, titulo, source_url, score, chunk_index }`

## Tests

Fixture de corpus pequeño + **Qdrant `:memory:`** (`QdrantClient(location=":memory:")`) o contenedor efímero; verificar orden y filtrado por score.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 `RecuperadorDenso` no usa BM25 ni lectura de markdown en disco
- [ ] #2 `crear_rag_tool()` retorna `StructuredTool` compatible con LangGraph tool-calling
- [ ] #3 Respuesta estructurada incluye `respuesta_contexto` y `fuentes` con campos requeridos
- [ ] #4 `top_k` y `score_minimo` leídos de settings (`RAG_TOP_K`, `RAG_SCORE_MINIMO`)
- [ ] #5 Tests con Qdrant in-memory pasan en CI sin API externa (mockear embeddings o usar dim fija con vector aleatorio controlado)
- [ ] #6 Manejo de colección vacía: mensaje claro para el compositor ("sin resultados")
- [ ] #7 Docstrings en español latinoamericano
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Implementar `RecuperadorDenso` sobre abstracción mínima del vector store LlamaIndex.
2. Mapear metadata de payload a `fuentes`.
3. Implementar `StructuredTool` con schema Pydantic de salida (o JSON schema) alineado al contrato.
4. Tests unitarios + integración in-memory.
5. Integración con router en task-56 (solo verificación de imports aquí).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Alinear umbral de score con la métrica devuelta por Qdrant/LlamaIndex (similaridad vs distancia); documentar conversión.
- Cuando no haya contexto suficiente, el compositor debe tender a responder literal **"No tengo información suficiente"** (política ya existente en `src/qa/prompt.py`); referenciar en descripción de tool o en meta-prompt task-55.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 `uv run pytest tests/rag/` verde
- [ ] #2 `ruff check` sin errores nuevos
- [ ] #3 Ejemplo de payload de fuentes validado contra schema frontend (task-59)
<!-- DOD:END -->
