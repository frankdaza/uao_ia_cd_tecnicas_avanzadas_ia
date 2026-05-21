---
id: TASK-60
title: 'Tests backend integrales (pytest) de la cadena agéntica, RAG y persistencia'
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-15 01:01'
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
- [x] #1 `uv run pytest` verde en CI local del proyecto tras migración M2
- [x] #2 Markers documentados; tests pesados no bloquean desarrollo sin Docker
- [x] #3 Cobertura listada en esta descripción alcanzada o justificada en notas
- [x] #4 Tests BM25 legacy eliminados o aislados sin dejar suite roja
- [x] #5 Fixtures reutilizables para AsyncClient FastAPI y DB
- [x] #6 Casos de error SSE y sesión inválida cubiertos
- [x] #7 `ruff check tests/` sin errores nuevos
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

Se añadió ``tests/conftest.py`` con documentación de markers, skip automático para ``integration_qdrant``, fixture ``fastapi_app_sesion_mock`` y helpers de sesión DB mock.

``pyproject.toml``: markers ``integration_qdrant`` y ``legacy_bm25``.

Tests BM25 bajo ``src/legacy`` marcados con ``legacy_bm25`` (``test_pipeline*``, ``test_recuperador_bm25``).

``tests/persistencia/test_repositorio_usuarios_unidad.py``: mocks de ``obtener_o_crear`` y ``actualizar_last_login``.

``tests/api/test_agente_stream.py``: 401 sin credencial, 403 ``session_id`` desalineado, 503 sin grafo, SSE ``error`` por ``MemoriaConexionError``.

``src/api/routers/agente.py``: ``MemoriaConexionError`` al crear memoria ahora emite evento SSE ``error`` (antes propagaba y rompía el stream).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Suite M2 consolidada: markers ``integration_qdrant`` y ``legacy_bm25`` documentados en ``pyproject.toml`` y ``tests/conftest.py`` (skip opcional para Qdrant en red). Fixture compartida ``fastapi_app_sesion_mock`` para FastAPI sin Postgres real; ``test_sesiones`` la reutiliza. Tests legacy BM25 etiquetados para excluir con ``pytest -m "not legacy_bm25"``. Nuevos tests: repositorio usuarios con sesión mock; agente SSE cubre 401/403/503 y evento ``error`` por fallo de memoria. Corrección en ``agente.py`` para capturar ``MemoriaConexionError`` al instanciar memoria y emitir SSE en lugar de fallar el transporte. ``uv run pytest`` y ``ruff check tests/`` verdes.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest` completo verde
- [x] #2 Sin warnings críticos nuevos de deprecación sin ticket
- [x] #3 Tiempo de suite razonable (<N minutos; documentar si crece)
<!-- DOD:END -->
