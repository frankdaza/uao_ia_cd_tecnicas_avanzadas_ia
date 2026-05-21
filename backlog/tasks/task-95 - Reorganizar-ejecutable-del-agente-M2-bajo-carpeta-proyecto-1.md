---
id: TASK-95
title: Reorganizar ejecutable del agente M2 bajo carpeta proyecto-1
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 05:50'
updated_date: '2026-05-21 05:57'
labels:
  - reorganizacion
  - monorepo
  - modulo-2
  - infraestructura
  - migracion
milestone: m-0
dependencies:
  - TASK-85
references:
  - src/
  - frontend/
  - scripts/
  - tests/
  - config/
  - alembic/
  - alembic.ini
  - pyproject.toml
  - uv.lock
  - .python-version
  - Dockerfile
  - docker-compose.yml
  - README.md
  - RESUMEN.md
  - informe/
  - .env.example
documentation:
  - .cursor/rules/project-structure.mdc
  - AGENTS.md
  - backlog/milestones/m-0 - agentic-final-project.md
  - >-
    backlog/tasks/task-85 -
    Auditoria-previa-de-imports-y-referencias-para-migracion-clean-enough-M2.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El milestone **m-0** (Agentic Final Project) requiere un workspace que permita futuros `proyecto-2/` sin mezclar corpus, backlog y tooling del producto actual. Hoy el ejecutable M2 (FastAPI, LangGraph, frontend React, Docker, Alembic, scripts de ingesta) vive en la raíz del repositorio junto a `data/` y `backlog/`.

## Objetivo

Reorganizar **todo el funcionamiento del proyecto actual** dentro de la carpeta **`proyecto-1/`**, dejando en la raíz solo:

- Carpetas de configuración de agentes/IDE: `.claude/`, `.cursor/`, `.vscode/`
- Gestión: `backlog/`
- Corpus compartido: `data/`
- Archivos de configuración Cursor/Claude: `.cursorignore`, `.cursorindexingignore`, `CLAUDE.md`, `AGENTS.md`
- Control de versiones: `.git/`, `.gitignore` (actualizado)

El código, tooling Python (`uv`), Node (`pnpm`), Docker, Alembic y documentación operativa del producto migran a `proyecto-1/`.

## Arquitectura objetivo

```
raiz/
  backlog/  data/  .cursor/  .claude/  .vscode/  CLAUDE.md  AGENTS.md
  proyecto-1/
    src/  frontend/  scripts/  tests/  config/
    alembic/  pyproject.toml  uv.lock  Dockerfile  docker-compose.yml
    README.md  .env.example  informe/
```

`data/` permanece en la raíz; el runtime en `proyecto-1/` debe resolver rutas `data/*` vía **workspace root** (un nivel arriba), no asumiendo que `pyproject.toml` y `data/` comparten el mismo directorio.

## Inventario de migración (git mv)

| Origen (raíz) | Destino |
|---------------|--------|
| `src/` | `proyecto-1/src/` |
| `frontend/` | `proyecto-1/frontend/` |
| `scripts/` | `proyecto-1/scripts/` |
| `tests/` | `proyecto-1/tests/` |
| `config/` | `proyecto-1/config/` |
| `alembic/`, `alembic.ini` | `proyecto-1/alembic/`, `proyecto-1/alembic.ini` |
| `pyproject.toml`, `uv.lock`, `.python-version` | `proyecto-1/` |
| `Dockerfile`, `docker-compose.yml` | `proyecto-1/` |
| `README.md`, `RESUMEN.md` | `proyecto-1/` |
| `informe/` | `proyecto-1/informe/` |
| `.env.example` | `proyecto-1/.env.example` |

`.env` local del desarrollador: ubicar en **`proyecto-1/.env`** (junto al compose). Documentar en README raíz breve que `docker compose` y `uv run` se ejecutan desde `proyecto-1/`.

## Punto crítico: resolución de rutas

Hoy `src/api/configuracion.py` usa `parents[2]` como raíz del repo y rutas como `data/structured/faqs.json`. Tras la migración:

1. **`parents[2]`** → raíz de **proyecto** (`proyecto-1/`).
2. Introducir **`UAO_WORKSPACE_ROOT`** (o equivalente): por defecto `proyecto-1.parent` si existe `../data/markdown`, con override por env.
3. Defaults `data/*` y `config/*` relativos al workspace o al proyecto según corresponda.
4. **Docker Compose**: volúmenes `../data/markdown`, `../data/structured`, `./config`.
5. Scripts: `encontrar_raiz_proyecto()` (pyproject.toml) + `encontrar_raiz_workspace()` (data compartido).
6. Tests con `Path(__file__).parents[2]`: unificar en fixtures `workspace_root` / `proyecto_root`.

## Fuera de alcance

- Mover `backlog/` o `data/` dentro de `proyecto-1/`.
- Refactors de arquitectura M2 (LangGraph, RAG, clean architecture); solo paths e infraestructura.
- Archivar con `task_complete` sin pedido explícito del usuario.
- Ejecutar esta reorganización dentro de otras tareas abiertas sin rebasar (coordinar con task-86 y similares).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Existe `proyecto-1/` con `src/`, `frontend/`, `scripts/`, `tests/`, `config/`, `alembic/`, `pyproject.toml`, `uv.lock`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `README.md`.
- [x] #2 La raíz no contiene duplicados de esas carpetas/archivos (salvo lo acordado en inventario).
- [x] #3 `uv run pytest` desde `proyecto-1/` pasa con el mismo baseline que antes de la migración (documentar skips/failures conocidos).
- [x] #4 `docker compose` desde `proyecto-1/` levanta API + Postgres + Qdrant; `/api/salud` OK; volúmenes montan `../data/markdown` y `../data/structured`.
- [x] #5 `pnpm --dir proyecto-1/frontend` dev y build producen `dist/`; proxy `/api` apunta a `:8000`.
- [x] #6 `uv run alembic upgrade head` funciona con cwd `proyecto-1/`.
- [x] #7 Scripts de ingesta (`indexar_corpus_qdrant.py`, etc.) resuelven corpus en `../data/markdown` sin flags manuales extra.
- [x] #8 Documentación: `proyecto-1/README.md` y README breve en raíz explicando layout; referencias rotas en skills/rules priorizadas o checklist en PR.
- [x] #9 Búsqueda `rg` sin referencias rotas a rutas antiguas (compose/Dockerfile en raíz, `parents[2]` asumiendo repo root para `data/`).
- [x] #10 `.gitignore` cubre artefactos bajo `proyecto-1/` (`.venv`, `node_modules`, `dist`, caches).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
**Fase 0 — Baseline**
- Crear rama `feat/proyecto-1-layout`.
- Capturar baseline: `uv run pytest -q` (conteo passed/skipped/failed), commit SHA actual.

**Fase 1 — Movimiento físico**
- `mkdir -p proyecto-1`.
- `git mv` de: `src`, `frontend`, `scripts`, `tests`, `config`, `alembic`, `alembic.ini`, `pyproject.toml`, `uv.lock`, `.python-version`, `Dockerfile`, `docker-compose.yml`, `README.md`, `RESUMEN.md`, `informe`, `.env.example` → bajo `proyecto-1/`.
- Añadir README mínimo en raíz: código en `proyecto-1/`, corpus en `data/`.

**Fase 2 — Resolución de rutas**
- `src/api/configuracion.py`: `workspace_root`, `.env` en `proyecto-1/`, rutas `data/*` vía workspace.
- `src/api/main.py`: `_FRONTEND_DIST` relativo a proyecto-1.
- Scripts (`encontrar_raiz_repo` en agrupar, indexar, eval, limpiar): `encontrar_raiz_proyecto()` + `encontrar_raiz_workspace()`.
- Tests: fixture `workspace_root` / `proyecto_root`; reemplazar `parents[2]` hardcodeados.
- Revisar `pyproject.toml` (`module-root`, pytest paths).

**Fase 3 — Docker y entorno**
- `Dockerfile`: contexto build desde `proyecto-1/`.
- `docker-compose.yml`: `build: .`, volúmenes `../data/markdown`, `../data/structured`, `./config`.
- Documentar en `proyecto-1/README.md`: `cd proyecto-1 && docker compose up --build`.

**Fase 4 — Frontend y DX**
- Verificar `vite.config.ts`, `package.json`, Playwright paths.
- Actualizar `scripts/README.md` y comandos en documentación operativa.

**Fase 5 — Validación y PR**
- Smoke: login, un turno SSE agente, ingesta `--limit 5`.
- `rg` por rutas rotas; actualizar tareas backlog que citen paths sin `proyecto-1/`.
- PR con checklist de comandos copiables.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Preferir **`git mv`** sobre copiar/borrar para preservar historial de git.
- Convención Python: identificadores en español ASCII; carpeta `proyecto-1` sin tilde.
- **Skills/rules** (`.cursor/`, `.claude/`): actualizar en esta tarea o dejar checklist explícito en PR si el diff es grande (`project-structure.mdc`, `AGENTS.md`, `CLAUDE.md`).
- **Cursor indexing**: revisar `.cursorindexingignore` para `proyecto-1/frontend/dist` y caches.
- Coordinar con **task-86** (reorganizar src/rag) y migraciones clean: ejecutar esta tarea **antes** o rebasar ramas dependientes.

## Riesgos y mitigación

| Riesgo | Mitigación |
|--------|------------|
| `parents[N]` hardcodeados | Fixture única + grep en validación |
| Compose ejecutado desde raíz antigua | README raíz + mensaje claro si falta `../data` |
| Paths en informe LaTeX | `rg` en `informe/` por `src/`, `data/` |
| Terminal del IDE en raíz | Documentar `cd proyecto-1` |
| Tareas backlog con rutas viejas | AC #9 + actualización puntual |

## Comandos de verificación (post-migración)

```bash
cd proyecto-1
uv sync
uv run pytest -q
uv run alembic upgrade head
docker compose up --build -d
curl -fsS http://127.0.0.1:8000/api/salud
pnpm --dir frontend install && pnpm --dir frontend build
uv run python scripts/indexar_corpus_qdrant.py --limit 5 ...  # según flags del README
```
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Migracion completada: ejecutable bajo proyecto-1/ (git mv de src, frontend, scripts, tests, config, alembic, Docker, pyproject, informe). data/ y backlog/ permanecen en raiz. Nuevo src/rutas_workspace.py (UAO_WORKSPACE_ROOT, encontrar_raiz_proyecto/workspace). docker-compose monta ../data/markdown y ../data/structured. README raiz + actualizacion AGENTS.md, project-structure.mdc, scripts/README. Baseline pytest desde proyecto-1: 396 passed, 9 skipped (igual que pre-migracion).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Al cierre: status Done vía task_edit; sin task_complete salvo pedido explícito.
- [x] #2 Sin secretos ni API keys en la tarea ni en commits.
- [x] #3 PR con comandos de verificación copiables desde `proyecto-1/`.
<!-- DOD:END -->
