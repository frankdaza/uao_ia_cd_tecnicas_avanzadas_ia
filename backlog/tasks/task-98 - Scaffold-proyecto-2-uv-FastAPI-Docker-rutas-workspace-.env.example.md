---
id: TASK-98
title: 'Scaffold proyecto-2 (uv, FastAPI, Docker, rutas workspace, .env.example)'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:15'
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
priority: high
ordinal: 2020
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

`proyecto-2/` aún no existe. Debe arrancar con el mismo estándar que `proyecto-1/` (Python 3.12.12, uv, Docker) pero como aplicación independiente TAAM.

## Objetivo

Crear el esqueleto ejecutable de `proyecto-2/` listo para desarrollo y compose, sin lógica de negocio aún.

## Layout mínimo

```
proyecto-2/
  pyproject.toml  # python ==3.12.12
  .python-version
  uv.lock
  .env.example
  docker-compose.yml  # app + postgres + qdrant (puertos distintos a proyecto-1 si coexisten)
  Dockerfile
  README.md
  src/
    api/main.py  # FastAPI health
    rutas_workspace.py  # copiar/adaptar patrón UAO_WORKSPACE_ROOT
  frontend/  # carpeta vacía o placeholder package.json
  scripts/
  tests/
```

## Reglas críticas

- **No** importar `proyecto-1` como paquete en runtime; solo copiar utilidades puntuales documentadas.
- `data/` sigue en **raíz del workspace**; rutas `data/taam/` o subcarpeta acordada en ADR para PDFs y FAQs.
- Puertos: documentar en README si compose M2 (8000) y TAAM (p. ej. 8001/5433/6334) corren en paralelo.
- Variables en `.env.example`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `DATABASE_URL`, `QDRANT_URL`, `OPENAI_API_KEY`, `ADMIN_API_KEY`, `ALLOWED_ORIGINS` — sin valores reales.

## README raíz workspace

Actualizar `README.md` raíz con sección `proyecto-2/` y comandos `cd proyecto-2 && uv sync`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Existe proyecto-2/ con pyproject.toml fijando Python 3.12.12 y uv.lock versionado
- [ ] #2 uv run uvicorn arranca GET /api/salud (o equivalente) desde proyecto-2/
- [ ] #3 docker compose up levanta app + postgres + qdrant sin conflicto documentado con proyecto-1
- [ ] #4 rutas_workspace resuelve data/ en raíz del workspace (UAO_WORKSPACE_ROOT)
- [ ] #5 .env.example lista todas las variables TAAM sin secretos
- [ ] #6 README.md de proyecto-2 explica relación con proyecto-1 y milestone m-0
<!-- AC:END -->
