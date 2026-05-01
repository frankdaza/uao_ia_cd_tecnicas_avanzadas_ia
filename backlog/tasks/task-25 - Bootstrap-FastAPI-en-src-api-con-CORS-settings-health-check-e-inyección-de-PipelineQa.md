---
id: TASK-25
title: >-
  Bootstrap FastAPI en src/api/ con CORS, settings, health-check e inyección de
  PipelineQa
status: Done
assignee: []
created_date: '2026-04-30 05:43'
updated_date: '2026-04-30 05:58'
labels:
  - backend
  - api
  - fastapi
dependencies:
  - TASK-21
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El pipeline Q&A existe en `src/qa/pipeline.py` pero solo es accesible desde Gradio. Para que el frontend React lo consuma, se necesita una capa HTTP. Se elige FastAPI + Uvicorn + sse-starlette.

## Objetivo

Crear la estructura base de `src/api/`:
- `src/api/__init__.py`
- `src/api/main.py`: app FastAPI con CORSMiddleware, lifespan (inicializa PipelineQa una vez), router montado en /api
- `src/api/configuracion.py`: Settings con pydantic-settings, lectura de .env
- `src/api/dependencias.py`: Depends(obtener_pipeline) que retorna el PipelineQa singleton
- `src/api/routers/__init__.py`
- `src/api/routers/salud.py`: GET /api/salud
- `src/api/esquemas.py`: modelos Pydantic v2 de request/response base

Dependencias Python: `uv add fastapi uvicorn[standard] sse-starlette pydantic-settings`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 src/api/ creado con estructura de módulos descrita
- [ ] #2 GET /api/salud devuelve {"estado": "ok", "version": "1.0.0"} con status 200
- [ ] #3 CORS configurable: ALLOWED_ORIGINS en .env (default: http://localhost:5173)
- [ ] #4 PipelineQa se instancia UNA sola vez en el lifespan de FastAPI y se inyecta vía Depends
- [ ] #5 uv run uvicorn src.api.main:app --reload inicia sin errores
- [ ] #6 fastapi, uvicorn, sse-starlette y pydantic-settings en pyproject.toml y uv.lock
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Creado src/api/ con __init__.py, main.py (lifespan + CORS + routers + StaticFiles para frontend), configuracion.py (pydantic-settings), dependencias.py (obtener_pipeline), esquemas.py (Pydantic v2: PeticionQa, RespuestaQa, RespuestaModelos, eventos SSE), routers/__init__.py, routers/salud.py (GET /api/salud). Dependencias instaladas: fastapi 0.136.1, uvicorn[standard], sse-starlette, pydantic-settings. uv run python -c 'from src.api.main import app' pasa sin errores.
<!-- SECTION:FINAL_SUMMARY:END -->
