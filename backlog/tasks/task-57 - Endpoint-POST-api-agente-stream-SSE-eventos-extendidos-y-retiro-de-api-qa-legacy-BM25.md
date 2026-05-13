---
id: TASK-57
title: >-
  Endpoint POST /api/agente/stream (SSE), eventos extendidos y retiro de /api/qa
  legacy BM25
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-13 00:58'
labels:
  - fastapi
  - sse
  - api
  - modulo-2
dependencies:
  - TASK-49
  - TASK-56
references:
  - src/api/routers/agente.py
  - src/api/esquemas.py
  - src/api/main.py
  - src/api/factoria_grafo_agente.py
  - src/api/dependencias.py
  - src/legacy/qa/pipeline.py
  - src/legacy/retrieval/
  - tests/api/test_agente_stream.py
documentation:
  - .claude/skills/fastapi-sse-api/SKILL.md
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El producto M2 centraliza el streaming en el **agente**; los endpoints BM25 (`POST /api/qa`, `POST /api/qa/stream`) deben **eliminarse del registro** y el código asociado retirarse o moverse a **`legacy/`** según política del equipo, dejando de leer `data/markdown/` en runtime.

## Objetivo

1. Crear **`src/api/routers/agente.py`** con `POST /api/agente/stream` y body **`PeticionAgente`**: `{ session_id, pregunta, primer_turno?: bool }` (+ campos mínimos de modelo si se centralizan en settings).

2. Extender **`src/api/esquemas.py`** con eventos SSE nuevos:
   - `EventoPensamiento` — tool candidata + razón
   - `EventoHerramienta` — nombre + latencia ms
   - `EventoToken` — delta texto, `motor="agente"`
   - `EventoFuentes` — chunks Qdrant serializados
   - `EventoFinal` — métricas agregadas opcionales
   - `EventoError` — código + mensaje seguro

3. **Lifespan / wiring**: montar router agente; **desmontar** `qa.py` del `main.py`.

4. **Eliminar o mover a legacy**: `src/api/routers/qa.py`, `src/qa/pipeline.py`, `src/retrieval/` (según decisión de conservar historial git vs borrado físico; el plan pide retiro del runtime productivo).

5. **Cancelación**: al desconectar el cliente SSE, cancelar la tarea del grafo/async generator de forma cooperativa.

6. Tests `httpx.AsyncClient` con grafo mockeado o dependencia override.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `POST /api/agente/stream` responde `text/event-stream` y emite secuencia coherente de eventos
- [x] #2 `/api/qa` y `/api/qa/stream` ya no están registrados en la app productiva
- [x] #3 Código BM25 (`pipeline.py`, `routers/qa.py`, `retrieval/`) fuera del import path del servidor o en `legacy/` claramente marcado
- [x] #4 Esquemas Pydantic de eventos validan payloads en tests
- [x] #5 Desconexión cliente cancela streaming sin traceback ruidoso
- [x] #6 OpenAPI documenta el nuevo endpoint y ejemplos
- [x] #7 Tests API nuevos en `tests/api/test_agente_stream.py`
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Definir contratos Pydantic de petición y eventos SSE (nombres de campo estables para frontend).
2. Implementar endpoint con `EventSourceResponse` / patrón existente del repo.
3. Integrar `crear_grafo_agente` y mapear `astream_events` → SSE.
4. Retirar router QA y limpiar `main.py`, dependencias y tests obsoletos (coord. task-60).
5. Añadir tests con cliente async y mock del grafo.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Endpoint POST /api/agente/stream con EventSourceResponse, eventos pensamiento/herramienta/token/fuentes/final/error (Pydantic en esquemas.py). Grafo compilado en lifespan vía factoria_grafo_agente.py; dependencia obtener_grafo_agente. BM25 movido a src/legacy/retrieval y pipeline a src/legacy/qa/pipeline.py; router qa eliminado del registro. corpus.py sin PipelineQa; recargar-corpus documenta ingesta Qdrant. Cancelación: is_disconnected + aclose del async generator astream_events. Tests: tests/api/test_agente_stream.py (grafo fake + memoria monkeypatch). tests/api/test_qa.py y test_stream.py eliminados; test_concurrent_openai_sampling eliminado. Frontend sigue en /api/qa/stream hasta task-59.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se implementó POST /api/agente/stream (SSE) con eventos extendidos y mapeo desde astream_events v2; se retiró el router QA/BM25 del servidor, se movió recuperación BM25 y pipeline M1 a src/legacy/, y se ajustaron tests y corpus. pnpm test del frontend puede seguir apuntando a /api/qa/stream hasta la migración en task-59.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest tests/api/test_agente_stream.py` verde
- [ ] #2 `pnpm --dir frontend test` puede fallar hasta task-59 — documentar orden; al cerrar M2 ambos verdes
- [x] #3 `ruff check` sin errores nuevos
- [ ] #4 Smoke manual: stream completo con sesión válida
<!-- DOD:END -->
