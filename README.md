# Workspace — Técnicas avanzadas de IA (UAO)

Repositorio multi-proyecto para el curso. El **código ejecutable del Módulo 2** vive en [`proyecto-1/`](proyecto-1/); el **corpus y datos compartidos** en [`data/`](data/); la gestión de tareas en [`backlog/`](backlog/).

## Estructura

| Ruta | Contenido |
|------|-----------|
| `proyecto-1/` | FastAPI, agente LangGraph, frontend React, Docker, Alembic, scripts, tests |
| `data/` | `raw/`, `markdown/`, `structured/`, `processed/`, `eval/` |
| `backlog/` | Tareas, milestones, ADRs, documentación del proyecto |
| `.cursor/`, `.claude/`, `AGENTS.md`, `CLAUDE.md` | Configuración de agentes e IDE |

## Comandos habituales

Desde **`proyecto-1/`** (donde están `pyproject.toml` y `docker-compose.yml`):

```bash
cd proyecto-1
uv sync
uv run pytest
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
docker compose up --build
pnpm --dir frontend install
pnpm --dir frontend dev
```

Variables de entorno: copiar `proyecto-1/.env.example` a `proyecto-1/.env`. Opcional en la raíz del repo: `UAO_WORKSPACE_ROOT` apunta al directorio que contiene `data/` (por defecto se infiere como el padre de `proyecto-1/`).

Documentación operativa completa: [`proyecto-1/README.md`](proyecto-1/README.md).
