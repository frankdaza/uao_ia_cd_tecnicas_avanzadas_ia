---
id: TASK-98
title: 'Scaffold proyecto-2 (uv, FastAPI, Docker, rutas workspace, .env.example)'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:15'
updated_date: '2026-05-21 22:50'
labels:
  - modulo-3
  - taam
  - proyecto-2
  - infraestructura
milestone: m-0
dependencies:
  - TASK-96
references:
  - proyecto-1/pyproject.toml
  - proyecto-1/docker-compose.yml
  - proyecto-1/src/rutas_workspace.py
  - README.md
documentation:
  - .claude/skills/uv-python-env/SKILL.md
  - .cursor/rules/project-structure.mdc
modified_files:
  - proyecto-2/
  - data/taam/.gitkeep
  - README.md
  - >-
    backlog/tasks/task-98 -
    Scaffold-proyecto-2-uv-FastAPI-Docker-rutas-workspace-.env.example.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Tras [TASK-96](task-96) / [decision-7](../../decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md), el MVP **TAAM** (Bot posoperatorio, Módulo 3) debe vivir en **`proyecto-2/`** como aplicación **independiente** de `proyecto-1/` (M2 LangGraph + SSE). Hoy la carpeta no existe; las tareas TASK-99+ (Alembic, agente, Telegram, frontend) dependen de un esqueleto ejecutable con el mismo estándar operativo: **Python 3.12.12**, **uv**, **FastAPI**, **Docker Compose** y resolución de `data/` en la raíz del workspace.

## Objetivo

Entregar un **scaffold mínimo pero real**: arranque local con `uv run uvicorn`, health-check `GET /api/salud`, `docker compose up` con **app + PostgreSQL + Qdrant** en puertos que no choquen con M2 si ambos stacks corren en paralelo, y plantilla `.env.example` sin secretos. **Sin** lógica de negocio TAAM (agente, webhook, OLTP, ingesta PDF).

## Alcance incluido

| Área | Entregable |
|------|------------|
| Python | `pyproject.toml` (`requires-python == 3.12.12`), `.python-version`, `uv.lock`, paquete `src` con `uv_build` |
| API | `src/api/main.py`, router `salud`, `pydantic-settings` mínimo en `configuracion.py` |
| Workspace | `src/rutas_workspace.py` (copia adaptada de `proyecto-1`; **sin** importar `proyecto-1` en runtime) |
| Docker | `Dockerfile` (solo backend), `docker-compose.yml` (postgres + qdrant + api) |
| Config | `.env.example` con variables TAAM documentadas |
| Tests | `pytest`: imports, rutas workspace, `GET /api/salud` con `httpx` |
| Docs | `proyecto-2/README.md` + sección en `README.md` raíz |
| Placeholder | `frontend/package.json` mínimo, carpetas `scripts/` y `tests/` |

## Layout objetivo

```
proyecto-2/
  pyproject.toml
  .python-version
  uv.lock
  .env.example
  docker-compose.yml
  Dockerfile
  README.md
  src/
    rutas_workspace.py
    configuracion.py
    api/
      main.py
      esquemas.py
      routers/salud.py
  frontend/package.json   # placeholder TASK-109
  scripts/
  tests/
```

## Reglas críticas

- **Prohibido** `import` desde el paquete de `proyecto-1` en runtime; solo reutilizar **patrones** (p. ej. `rutas_workspace.py`) copiados y comentados.
- Corpus y PDFs: `data/` permanece en la **raíz del repo** (`UAO_WORKSPACE_ROOT` o padre de `proyecto-2/` con `data/markdown/`). Subcarpeta prevista para TAAM: `data/taam/` (crear vacía opcional con `.gitkeep`).
- **Puertos por defecto en paralelo con M2** (documentar en README):
  - M2: API **8000**, Postgres host **15432**, Qdrant REST host **6333**
  - TAAM: API **8001**, Postgres host **15433**, Qdrant REST host **6334**, gRPC host **6335**, Vite futuro **5174**
- Nombre del proyecto en health: `proyecto: taam`, `version: 0.1.0`.

## Fuera de alcance (tareas siguientes)

- Alembic / tablas OLTP → TASK-99
- Agente LangChain, `POST /chat`, Telegram → TASK-103–106
- Frontend React completo → TASK-109
- Ingesta PDF / colección `taam_protocolos` → TASK-101

## Referencias

- [decision-7](../../decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md) (diagrama despliegue y puertos)
- Espejo operativo: `proyecto-1/pyproject.toml`, `docker-compose.yml`, `src/rutas_workspace.py`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 Existe `proyecto-2/` con `pyproject.toml` que fija `requires-python = "==3.12.12"`, `.python-version` con `3.12.12` y `uv.lock` versionado en git
- [x] #2 #2 Desde `proyecto-2/`, `uv sync` y `uv run uvicorn src.api.main:app --host 127.0.0.1 --port 8001` exponen `GET /api/salud` con JSON `estado: ok` y campo que identifique el proyecto TAAM
- [x] #3 #3 `docker compose up --build` en `proyecto-2/` levanta servicios `api`, `postgres` y `qdrant`; el healthcheck de `api` pasa contra `/api/salud`; puertos publicados por defecto no colisionan con `proyecto-1` (tabla en README)
- [x] #4 #4 `src/rutas_workspace.py` resuelve rutas bajo la raíz del workspace: con `UAO_WORKSPACE_ROOT` apunta ahí; sin override, el padre de `proyecto-2/` que contiene `data/markdown/`; prueba `tests/test_rutas_workspace.py` en verde
- [x] #5 #5 `.env.example` documenta sin valores reales: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `DATABASE_URL`, `QDRANT_URL`, `OPENAI_API_KEY`, `ADMIN_API_KEY`, `ALLOWED_ORIGINS`, más variables de compose (`API_PORT`, `POSTGRES_*`, `QDRANT_*`, `UAO_WORKSPACE_ROOT` opcional)
- [x] #6 #6 `proyecto-2/README.md` explica relación con `proyecto-1`, milestone m-0, comandos `uv`/`compose` y coexistencia de puertos; `README.md` raíz del repo incluye fila/comandos para `proyecto-2`
- [x] #7 #7 `uv run pytest` en `proyecto-2/` pasa al menos tests de entorno, rutas workspace y salud HTTP
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Plan de implementación

1. **Metadatos Backlog** — Ampliar descripción, AC (#1–#7), DoD y este plan (hecho antes de codificar).
2. **Manifiesto uv** — Crear `pyproject.toml` (nombre `uao-taam`, deps mínimas: fastapi, uvicorn, pydantic-settings, python-dotenv; dev: pytest, httpx), `.python-version`, `src/__init__.py`.
3. **Rutas workspace** — Copiar/adaptar `proyecto-1/src/rutas_workspace.py` (comentarios `proyecto-2`); añadir `data/taam/.gitkeep` en workspace si no existe.
4. **API mínima** — `configuracion.py` (settings), `esquemas.RespuestaSalud`, `routers/salud.py`, `api/main.py` con CORS desde `ALLOWED_ORIGINS`.
5. **Docker** — `Dockerfile` slim (uv sync, puerto 8001); `docker-compose.yml` con postgres:15433, qdrant:6334/6335, api:8001, volúmenes `../data/taam` opcional read-only.
6. **`.env.example`** — Variables TAAM + compose; comentarios de puertos paralelos M2.
7. **Tests** — `test_entorno_inicial.py`, `test_rutas_workspace.py`, `test_api_salud.py` (TestClient/httpx).
8. **Documentación** — `proyecto-2/README.md`; actualizar `README.md` raíz.
9. **Validación** — `uv sync`, `uv run pytest`, arranque uvicorn manual o test; `docker compose config` (y `up` si el entorno lo permite).
10. **Cierre** — `task_edit`: marcar AC, `notesAppend`, `status: Done` (sin `task_complete`).

## Riesgos

- Colisión de puertos si el desarrollador personalizó M2: mitigar documentando overrides en README.
- Docker no disponible en CI del curso: AC #3 verificable localmente; tests HTTP cubren AC #2 sin compose.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
ADR vigente: decision-7 (no decision-4). Health sin `agente_mock_llm` (específico M2). Compose TAAM sin `db-init`/Alembic hasta TASK-99. Frontend solo placeholder hasta TASK-109.

2026-05-21: Plan y AC ampliados; inicio de scaffold en repo.

Dockerfile: mkdir /home/app y UV_CACHE_DIR=/app/.cache/uv para evitar Permission denied con `uv run` como usuario app.

Compose verificado: curl http://127.0.0.1:8001/api/salud desde host tras `docker compose up --build -d`.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Scaffold `proyecto-2/` entregado: pyproject.toml (Python 3.12.12), uv.lock, FastAPI `GET /api/salud` (`proyecto: taam`), `rutas_workspace.py`, docker-compose (API 8001, Postgres 15433, Qdrant 6334/6335), Dockerfile corregido (permisos usuario `app` + UV_CACHE_DIR), `.env.example`, tests pytest (5 OK), `data/taam/.gitkeep`, README proyecto-2 y sección en README raíz. Validado: `uv run pytest`, uvicorn local, `docker compose up` + health.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Código y lockfile commiteables; sin secretos en `.env.example` ni en la tarea
- [x] #2 README de `proyecto-2` enlaza decision-7 y lista explícitamente qué queda para TASK-99+
- [x] #3 Notas de implementación y plan actualizados en la tarea; criterios de aceptación marcados al cerrar
<!-- DOD:END -->
