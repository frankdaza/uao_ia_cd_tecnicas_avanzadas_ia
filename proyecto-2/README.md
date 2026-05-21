# proyecto-2 — TAAM (Bot posoperatorio, Módulo 3)

Aplicación **independiente** del asistente M2 en [`proyecto-1/`](../proyecto-1/). Implementa el MVP **TAAM** según [decision-7](../backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md) (Ruta A LangChain, Telegram vía 2, `POST /chat` en tareas posteriores).

**Milestone:** [m-0 — Agentic Final Project](../backlog/milestones/m-0%20-%20agentic-final-project.md).

## Relación con proyecto-1

| Tema | proyecto-1 (M2) | proyecto-2 (TAAM) |
|------|-----------------|-------------------|
| Agente | LangGraph + SSE | LangChain `create_agent` (TASK-103+) |
| API conversacional | `POST /api/agente/stream` | `POST /chat` (TASK-104) |
| Postgres OLTP | `app` en `:15432` (tablas `usuarios`, `config_admin_m2`, …) | Base **`taam`** en `:15433` (tablas `tipos_procedimiento`, `casos_postoperatorio`, `vinculos_telegram`, `alertas_triage`, …). **No compartir** `DATABASE_URL` con M2. |
| Qdrant | Instancias y colecciones M2 | Instancias y colección `taam_protocolos` dedicadas |
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

### Catálogo de procedimientos (UC-MVP-01)

Rutas bajo `/api/admin/procedimientos` (cabecera **`X-Admin-Key`** = `ADMIN_API_KEY`):

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/admin/procedimientos` | Multipart: `metadata` (JSON `codigo`, `nombre`) + `archivo` (PDF) |
| `GET` | `/api/admin/procedimientos` | Listado (`limit`, `offset`) |
| `GET` | `/api/admin/procedimientos/{id}` | Detalle |
| `PATCH` | `/api/admin/procedimientos/{id}` | Actualizar metadata y/o reemplazar PDF |
| `POST` | `/api/admin/procedimientos/{id}/reindexar` | Relanza ingesta Qdrant (202) |

Los PDF se guardan en **`data/taam/procedimientos/{uuid}/protocolo.pdf`** (workspace; volumen Docker montado en `/app/data/taam`). Tamaño máximo por defecto: **10 MB** (`TAAM_PDF_MAX_MB`). Tras subir o reemplazar PDF, la API encola ingesta en segundo plano; `indexacion_estado` pasa a `ok` o `error` cuando termina.

### Ingesta PDF → Qdrant (`taam_protocolos`)

- **Stack:** `pdfplumber` + `RecursiveCharacterTextSplitter` (800 / 120) + `OpenAIEmbeddings` + `langchain_qdrant.QdrantVectorStore`.
- **Colección dedicada** (no `corpus_*` de M2): `TAAM_QDRANT_COLLECTION` (default `taam_protocolos`), REST en host **6334**.
- **CLI:** `uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid>` o `--todos-pendientes`.
- **Limitación:** PDF escaneado sin OCR puede quedar sin texto suficiente → `indexacion_estado=error`.

Ejemplo local:

```bash
export ADMIN_API_KEY='cambiar-por-clave-segura'
curl -sS -H "X-Admin-Key: $ADMIN_API_KEY" \
  -F 'metadata={"codigo":"cole-lap","nombre":"Colecistectomia laparoscopica"};type=application/json' \
  -F "archivo=@protocolo.pdf;type=application/pdf" \
  http://127.0.0.1:8001/api/admin/procedimientos | jq .
```

### Casos postoperatorio y emparejamiento Telegram (UC-MVP-02)

Rutas staff bajo `/api/staff/casos` (cabecera **`X-Staff-Key`** = `STAFF_API_KEY`). El emparejamiento lo invoca el webhook Telegram (**TASK-106**) con **`X-Telegram-Bot-Api-Secret-Token`** = `TELEGRAM_WEBHOOK_SECRET`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/staff/casos` | Alta de caso (`estado=activo`); exige `tipo_procedimiento` con `indexacion_estado=ok` |
| `GET` | `/api/staff/casos` | Listado (`estado`, `limit`, `offset`); incluye `vinculado_telegram` |
| `POST` | `/api/staff/casos/{id}/codigo-emparejamiento` | Código 6–8 caracteres, TTL 24 h (`TAAM_CODIGO_EMPAREJAMIENTO_TTL_HORAS`) |
| `POST` | `/api/telegram/emparejar` | Body: `codigo`, `telegram_chat_id`; respuesta con `mensaje_confirmacion` o error `codigo_expirado` |

Flujo demo: crear caso → generar código → en Telegram `/start CODIGO` (webhook llama `emparejar`) → listado muestra **Vinculado Telegram: sí**.

```bash
export STAFF_API_KEY='cambiar-por-clave-segura'
export TELEGRAM_WEBHOOK_SECRET='cambiar-por-secreto-webhook'

curl -sS -H "X-Staff-Key: $STAFF_API_KEY" -H "Content-Type: application/json" \
  -d '{"paciente_doc_id":"CC-1","paciente_nombre":"Paciente Demo","tipo_procedimiento_id":"<uuid-ok>","cirujano_id":"M1","cirujano_nombre":"Dr. Demo","fecha_cirugia":"2026-05-15"}' \
  http://127.0.0.1:8001/api/staff/casos | jq .
```

Auth JWT staff (**TASK-105**) sustituirá `X-Staff-Key` en el panel React (**TASK-112**).

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

Tras levantar Postgres, aplicar el esquema OLTP antes de usar APIs que lean/escriban casos o alertas:

```bash
cd proyecto-2
# Con compose en marcha (Postgres en localhost:15433):
export DATABASE_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:15433/taam'
uv run alembic upgrade head

# Dentro del contenedor API:
docker compose exec api uv run alembic upgrade head
```

El healthcheck de la API **no** sustituye las migraciones; solo valida `GET /api/salud`.

## Variables de entorno

Plantilla: [`.env.example`](.env.example). Base de datos: `DATABASE_URL` (compose suele usar `postgres://…`; el backend lo normaliza a `postgresql+asyncpg://`) o bien `POSTGRES_HOST`, `POSTGRES_PORT` (defecto **15433**), `POSTGRES_DB` (`taam`), `POSTGRES_USER`, `POSTGRES_PASSWORD`.

Otras variables M3: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `QDRANT_URL`, `OPENAI_API_KEY`, `ADMIN_API_KEY`, `STAFF_API_KEY`, `TAAM_CODIGO_EMPAREJAMIENTO_TTL_HORAS`, `TAAM_CODIGO_LONGITUD`, `TAAM_PDF_MAX_MB`, `TAAM_QDRANT_COLLECTION`, `TAAM_CHUNK_SIZE`, `TAAM_CHUNK_OVERLAP`, `EMBEDDING_MODEL`, `INGESTA_REINTENTOS`, `INGESTA_BACKOFF_MAX_SEG`, `ALLOWED_ORIGINS`.

Opcional: `UAO_WORKSPACE_ROOT` apunta al directorio que contiene `data/` (por defecto se infiere como el padre de `proyecto-2/`).

## Estructura

```
src/api/              # FastAPI (salud, admin, staff/casos, telegram/emparejar)
src/ingesta/          # ingesta PDF → Qdrant (LangChain)
src/rag/              # vector store TAAM
src/persistencia/     # modelos SQLAlchemy, motor async, repositorios (TASK-99)
src/configuracion.py
src/rutas_workspace.py
alembic/versions/     # migraciones OLTP TAAM
frontend/             # placeholder hasta TASK-109
scripts/              # `ingestar_protocolo_pdf.py`, demo (TASK-114)
tests/                # API, ingesta, persistencia
```

## Próximas tareas Backlog
- **TASK-103–106** — Agente, `/chat`, webhook Telegram
- **TASK-109** — Frontend React

Casos de uso: [Caso de Uso TAAM](../backlog/docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md).
