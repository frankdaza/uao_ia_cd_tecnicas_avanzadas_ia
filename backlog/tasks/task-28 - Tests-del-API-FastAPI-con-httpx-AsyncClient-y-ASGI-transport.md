---
id: TASK-28
title: Tests del API FastAPI con httpx AsyncClient y ASGI transport
status: Done
assignee: []
created_date: '2026-04-30 05:44'
updated_date: '2026-04-30 06:01'
labels:
  - tests
  - backend
  - api
dependencies:
  - TASK-27
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Crear suite de tests en `tests/api/` que cubra los endpoints FastAPI sin red real ni claves reales:

- `tests/api/__init__.py`
- `tests/api/conftest.py`: fixture `async_client` con `httpx.AsyncClient(app=app, base_url='http://test')`
- `tests/api/test_salud.py`: GET /api/salud
- `tests/api/test_modelos.py`: GET /api/modelos con mocks
- `tests/api/test_qa.py`: POST /api/qa happy paths y errores (Ollama caído, sin API key)
- `tests/api/test_stream.py`: POST /api/qa/stream y /api/qa/dual/stream; parseo de eventos SSE

Dependencias test: `uv add --group dev httpx anyio`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 tests/api/ creado con todos los archivos descritos
- [ ] #2 GET /api/salud retorna 200 con {estado: ok}
- [ ] #3 GET /api/modelos retorna estructura correcta con mocks de PipelineQa
- [ ] #4 POST /api/qa happy path Ollama retorna 200 con texto y fuentes
- [ ] #5 POST /api/qa con Ollama caído retorna 503 con detail en español
- [ ] #6 POST /api/qa/stream emite eventos SSE parseables (data: {"tipo": "token", ...})
- [ ] #7 POST /api/qa/dual/stream emite eventos con campo motor diferenciado
- [ ] #8 uv run pytest tests/api/ pasa sin red real ni claves reales
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Creados tests/api/__init__.py, conftest.py (fixture async_client con ASGITransport + pipeline mock), test_salud.py (2 tests), test_modelos.py (3 tests), test_qa.py (5 tests incluyendo Ollama caído 503), test_stream.py (4 tests de SSE). Instalados pytest-asyncio 1.3.0 y httpx (ya existía). 14 tests de API pasan. Suite global: 119 passed, 1 skipped.
<!-- SECTION:FINAL_SUMMARY:END -->
