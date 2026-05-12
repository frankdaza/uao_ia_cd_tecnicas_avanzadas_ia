---
id: TASK-57
title: Endpoint POST /api/agente/stream (SSE), eventos extendidos y retiro de /api/qa legacy BM25
status: To Do
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-11 00:00'
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
  - src/api/routers/qa.py
  - src/qa/pipeline.py
  - src/retrieval/
documentation:
  - .claude/skills/fastapi-sse-api/SKILL.md
priority: high
ordinal: 15000
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
- [ ] #1 `POST /api/agente/stream` responde `text/event-stream` y emite secuencia coherente de eventos
- [ ] #2 `/api/qa` y `/api/qa/stream` ya no están registrados en la app productiva
- [ ] #3 Código BM25 (`pipeline.py`, `routers/qa.py`, `retrieval/`) fuera del import path del servidor o en `legacy/` claramente marcado
- [ ] #4 Esquemas Pydantic de eventos validan payloads en tests
- [ ] #5 Desconexión cliente cancela streaming sin traceback ruidoso
- [ ] #6 OpenAPI documenta el nuevo endpoint y ejemplos
- [ ] #7 Tests API nuevos en `tests/api/test_agente_stream.py`
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
- Conservar `GET /api/salud` y utilidades no ligadas a BM25.
- Si el frontend aún no migró (task-59), coordinar feature flag o orden de merges.
- Corpus `data/markdown/` no se borra del repo; solo deja de leerse en API runtime.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 `uv run pytest tests/api/test_agente_stream.py` verde
- [ ] #2 `pnpm --dir frontend test` puede fallar hasta task-59 — documentar orden; al cerrar M2 ambos verdes
- [ ] #3 `ruff check` sin errores nuevos
- [ ] #4 Smoke manual: stream completo con sesión válida
<!-- DOD:END -->
