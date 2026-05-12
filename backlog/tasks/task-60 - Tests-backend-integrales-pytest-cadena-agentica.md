---
id: TASK-60
title: Tests backend integrales (pytest) de la cadena agéntica, RAG y persistencia
status: To Do
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-11 00:00'
labels:
  - pytest
  - qa
  - modulo-2
dependencies:
  - TASK-48
  - TASK-49
  - TASK-51
  - TASK-54
  - TASK-56
  - TASK-57
references:
  - tests/agentes/
  - tests/rag/
  - tests/persistencia/
  - tests/api/test_sesiones.py
  - tests/api/test_agente_stream.py
  - tests/qa/test_pipeline.py
documentation:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
priority: high
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La migración elimina BM25 del runtime; la suite de tests debe reflejar la **nueva superficie** (sesiones, agente SSE, tools, RAG denso, memoria) y retirar o aislar tests legacy del pipeline BM25.

## Objetivo

1. Crear/organizar suites bajo:
   - `tests/agentes/` — meta-prompt, FAQ tool, router con `FakeListChatModel`
   - `tests/rag/` — `RecuperadorDenso`, factories embeddings (mocks)
   - `tests/persistencia/` — repositorio usuarios (mock o contenedor)
   - `tests/api/test_sesiones.py`, `tests/api/test_agente_stream.py`

2. Cobertura mínima verificable:
   - Repositorio usuarios (`obtener_o_crear`, `last_login`)
   - Memoria con ventana `HISTORIAL_DIAS_MAX` / `HISTORIAL_TURNOS_MAX` (integration con Postgres opcional)
   - `FaqStructuredTool` positivos/negativos
   - `RecuperadorDenso` + `RagTool` con Qdrant `:memory:`
   - Router agente con LLM fake
   - Endpoint sesiones y endpoint agente SSE (mock grafo)

3. Introducir markers pytest: **`integration_postgres`**, **`integration_qdrant`** — skip automático si no hay servicios (documentar en `pytest.ini` o `conftest.py`).

4. **Legacy**: borrar o marcar como `legacy` / `xfail` tests que dependan exclusivamente de BM25 (`tests/qa/test_pipeline.py`, `tests/qa/test_pipeline_openai_dual.py`, tests de `recuperador.py` si existen), coordinando con task-57 para que `uv run pytest` quede **verde** en el estado final M2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 `uv run pytest` verde en CI local del proyecto tras migración M2
- [ ] #2 Markers documentados; tests pesados no bloquean desarrollo sin Docker
- [ ] #3 Cobertura listada en esta descripción alcanzada o justificada en notas
- [ ] #4 Tests BM25 legacy eliminados o aislados sin dejar suite roja
- [ ] #5 Fixtures reutilizables para AsyncClient FastAPI y DB
- [ ] #6 Casos de error SSE y sesión inválida cubiertos
- [ ] #7 `ruff check tests/` sin errores nuevos
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Inventariar tests rotos post task-57; clasificar delete vs rewrite.
2. Crear `tests/conftest.py` markers y fixtures compartidas.
3. Implementar tests por paquete en orden de dependencias.
4. Ejecutar `uv run pytest` completo y ajustar skips.
5. Documentar en README cómo correr integración (task-63 puede pulir).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Para SSE, considerar `httpx` stream y acumulación de eventos.
- Evitar llamadas reales a OpenAI en default CI; usar mocks/fakes.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 `uv run pytest` completo verde
- [ ] #2 Sin warnings críticos nuevos de deprecación sin ticket
- [ ] #3 Tiempo de suite razonable (<N minutos; documentar si crece)
<!-- DOD:END -->
