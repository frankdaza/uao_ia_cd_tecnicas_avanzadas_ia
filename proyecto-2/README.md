# proyecto-2 — TAAM (Bot posoperatorio, Módulo 3)

Aplicación **independiente** del asistente M2 en [`proyecto-1/`](../proyecto-1/). Implementa el MVP **TAAM** según [decision-7](../backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md) (Ruta A LangChain, Telegram vía 2, `POST /chat` en tareas posteriores).

**Milestone:** [m-0 — Agentic Final Project](../backlog/milestones/m-0%20-%20agentic-final-project.md).

## Relación con proyecto-1

| Tema | proyecto-1 (M2) | proyecto-2 (TAAM) |
|------|-----------------|-------------------|
| Agente | LangGraph + SSE | LangChain `create_agent` (TASK-103+) |
| API conversacional | `POST /api/agente/stream` | `POST /chat` (TASK-104) |
| Postgres / Qdrant | Instancias y colecciones M2 | Instancias y colección `taam_protocolos` dedicadas |
| Frontend | React en `proyecto-1/frontend/` | React nuevo en `proyecto-2/frontend/` (TASK-109) |
| Corpus | `data/markdown/`, `data/structured/` | PDFs y datos en `data/taam/` |

**No** importar código de `proyecto-1` en runtime; solo compartir el workspace (`data/` en la raíz del repo) vía `src/rutas_workspace.py`.

## Requisitos

- Python **3.12.12** (exacto)
- [uv](https://docs.astral.sh/uv/)
- Docker y Docker Compose (stack local opcional)

## Comandos rápidos

```bash
cd proyecto-2
cp .env.example .env   # completar secretos localmente
uv sync
uv run pytest
uv run uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8001
```

Health: `GET http://127.0.0.1:8001/api/salud` → `{"estado":"ok","version":"0.1.0","proyecto":"taam"}`.

## Docker Compose

```bash
cd proyecto-2
docker compose up --build
```

### Puertos por defecto (coexistencia con M2)

| Servicio | proyecto-1 (M2) | proyecto-2 (TAAM) |
|----------|-----------------|-------------------|
| API HTTP | 8000 | **8001** |
| Postgres (host) | 15432 | **15433** |
| Qdrant REST (host) | 6333 | **6334** |
| Qdrant gRPC (host) | 6334 | **6335** |
| Vite (dev) | 5173 | **5174** (previsto) |

Si algún puerto está ocupado, sobreescribir en `.env` (`API_PORT`, `POSTGRES_PUBLISH_PORT`, `QDRANT_REST_PORT`, etc.).

El compose actual **no** ejecuta migraciones Alembic (TASK-99); el healthcheck solo valida la API.

## Variables de entorno

Plantilla: [`.env.example`](.env.example). Obligatorias para funcionalidad completa M3 (cuando exista): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `DATABASE_URL`, `QDRANT_URL`, `OPENAI_API_KEY`, `ADMIN_API_KEY`, `ALLOWED_ORIGINS`.

Opcional: `UAO_WORKSPACE_ROOT` apunta al directorio que contiene `data/` (por defecto se infiere como el padre de `proyecto-2/`).

## Estructura (scaffold TASK-98)

```
src/api/          # FastAPI (salud; más routers en tareas M3)
src/rutas_workspace.py
frontend/         # placeholder hasta TASK-109
scripts/          # ingesta y demo (TASK-101, TASK-114)
tests/
```

## Próximas tareas Backlog

- **TASK-99** — Esquema Postgres + Alembic
- **TASK-103–106** — Agente, `/chat`, Telegram
- **TASK-109** — Frontend React
- **TASK-101** — Ingesta PDF → Qdrant `taam_protocolos`

Casos de uso: [Caso de Uso TAAM](../backlog/docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md).
