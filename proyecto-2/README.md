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

Rutas bajo `/api/admin/procedimientos`. Acceso: cabecera **`X-Admin-Key`** = `ADMIN_API_KEY` **o** JWT staff con `rol=admin` (`Authorization: Bearer` tras `POST /api/auth/staff/login`):

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

### Autenticación staff (JWT, TASK-105)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/auth/staff/login` | Body JSON `email`, `password` → `access_token` (JWT HS256, 8 h por defecto) |

Variables: `STAFF_JWT_SECRET` (obligatoria para auth staff), `STAFF_JWT_EXPIRE_HORAS` (opcional). Contraseñas demo solo en entorno local: `STAFF_DEMO_ASISTENTE_PASSWORD`, `STAFF_DEMO_CLINICO_PASSWORD`, `STAFF_DEMO_ADMIN_PASSWORD`.

Usuarios demo (tras migraciones y semilla):

| Email | Rol |
|-------|-----|
| `asistente@demo.taam` | `asistente` |
| `clinico@demo.taam` | `clinico` |
| `admin@demo.taam` | `admin` |

```bash
cd proyecto-2
export STAFF_JWT_SECRET='cambiar-por-secreto-jwt-min-32-caracteres'
uv run alembic upgrade head
uv run python -m scripts.sembrar_usuarios_staff_demo

TOKEN=$(curl -sS -X POST http://127.0.0.1:8001/api/auth/staff/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"asistente@demo.taam","password":"cambiar-demo-asistente"}' | jq -r .access_token)

curl -sS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8001/api/staff/casos | jq .
```

**Rate limit** en login: no implementado en MVP; en producción conviene limitar en proxy (nginx/Cloudflare).

`STAFF_API_KEY` / `X-Staff-Key` quedaron **deprecados**; el panel React (**TASK-112**) usará Bearer JWT en memoria de pestaña.

### Casos postoperatorio y emparejamiento Telegram (UC-MVP-02)

Rutas staff bajo `/api/staff/casos` (cabecera **`Authorization: Bearer`**). El emparejamiento lo invoca el webhook Telegram (**TASK-106**) con **`X-Telegram-Bot-Api-Secret-Token`** = `TELEGRAM_WEBHOOK_SECRET`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/staff/tipos-procedimiento` | Tipos con `indexacion_estado=ok` (`id`, `codigo`, `nombre`) para select de alta |
| `POST` | `/api/staff/casos` | Alta de caso (`estado=activo`); exige `tipo_procedimiento` con `indexacion_estado=ok` |
| `GET` | `/api/staff/casos` | Listado (`estado`, `limit`, `offset`); incluye `vinculado_telegram` |
| `POST` | `/api/staff/casos/{id}/codigo-emparejamiento` | Código 6–8 caracteres, TTL 24 h (`TAAM_CODIGO_EMPAREJAMIENTO_TTL_HORAS`) |
| `POST` | `/api/telegram/emparejar` | Body: `codigo`, `telegram_chat_id`; respuesta con `mensaje_confirmacion` o error `codigo_expirado` |

Flujo demo: login staff → crear caso → generar código → en Telegram `/start CODIGO` (webhook llama `emparejar`) → listado muestra **Vinculado Telegram: sí**.

### Seguimiento: alertas y conversaciones (UC-MVP-05 / TASK-108)

Panel staff (consumo desde **TASK-113**). Tag OpenAPI: **`staff-seguimiento`**. Historial desde **checkpointer** LangGraph (`thread_id` = `telegram:{chat_id}`), no tablas del Módulo 2.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/staff/alertas` | Bandeja (`revisado`, `severidad`, `caso_id`, `limit`, `offset`); orden urgente → seguimiento → info |
| `PATCH` | `/api/staff/alertas/{id}` | Body `{ "revisado": true }`; auditoría `revisado_at` + `revisado_staff_id` (idempotente) |
| `GET` | `/api/staff/casos/{id}/conversacion` | Mensajes human/assistant del hilo; `404` sin vínculo Telegram |
| `GET` | `/api/staff/casos/{id}/resumen` | Última alerta, conteo mensajes, próximo recordatorio pendiente |

Rol **`asistente`**: `paciente_doc_id` y `telegram_chat_id` enmascarados (últimos 4 caracteres). Migración **`0003_alertas_auditoria`**: índice `(revisado, created_at)` y FK de revisión.

### Webhook Telegram e integración vía 2 (TASK-106)

Canal canónico según [decision-7](../backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md). El mismo proceso FastAPI recibe updates, invoca el agente vía servicio interno de `POST /chat` y responde con `sendMessage`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/integracion/telegram/webhook` | Body: `Update` de Telegram; cabecera **`X-Telegram-Bot-Api-Secret-Token`** = `TELEGRAM_WEBHOOK_SECRET` |

Variables obligatorias para integración activa:

- `TELEGRAM_BOT_TOKEN` — token del bot (@BotFather).
- `TELEGRAM_WEBHOOK_SECRET` — secret que Telegram envía en cada update (y que usted define al registrar el webhook).

Registrar webhook (URL pública **HTTPS**; en local use ngrok o Cloudflare Tunnel):

```bash
cd proyecto-2
export TELEGRAM_BOT_TOKEN='...'
export TELEGRAM_WEBHOOK_SECRET='...'
uv run python -m scripts.configurar_webhook_telegram \
  --url 'https://TU-TUNEL.example/api/integracion/telegram/webhook'
```

**Polling:** no está implementado en el producto. Sin túnel HTTPS solo puede probarse con `httpx` contra el webhook (tests en `tests/api/test_telegram_webhook.py`) o enviando updates JSON manualmente.

Flujo paciente: `/start CODIGO` (emparejamiento) → mensajes de texto → respuesta del agente en Telegram. `session_id` del checkpointer: `telegram:{chat_id}`. Idempotencia: tabla `telegram_updates_procesados` (migración `0002`).

### Recordatorios proactivos Telegram (UC-MVP-04 / TASK-107)

Recordatorios de medicación/terapia según **plantillas** por `tipo_procedimiento` y **`fecha_cirugia`** del caso. **Sin email** ni agenda hospitalaria en MVP.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/staff/casos/{id}/disparar-recordatorio-prueba` | Envía el siguiente recordatorio pendiente (demo sin esperar el scheduler) |

Al crear un caso (`POST /api/staff/casos`) se insertan plantillas semilla si el tipo no tenía ninguna y se programan filas en `recordatorios_enviados` (`programado_at = fecha_cirugia + offset_horas`).

Job interno (asyncio en el lifespan de FastAPI): cada `RECORDATORIOS_JOB_INTERVAL_SEG` (default 60) busca pendientes con `programado_at <= now()` y envía por la misma Bot API que TASK-106. Si el caso no tiene vínculo Telegram, omite y registra log.

Variables:

- `RECORDATORIOS_JOB_HABILITADO` — `true`/`false` (en tests suele ir en `false`).
- `RECORDATORIOS_JOB_INTERVAL_SEG` — intervalo del job en segundos.

Placeholders en `texto_plantilla`: `{nombre_paciente}`, `{tipo_procedimiento}`, `{texto_cuidado}`.

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

Otras variables M3: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `QDRANT_URL`, `OPENAI_API_KEY`, `AGENTE_MODELO`, `AGENTE_RAG_K`, `ADMIN_API_KEY`, `STAFF_JWT_SECRET`, `STAFF_JWT_EXPIRE_HORAS`, `STAFF_DEMO_*_PASSWORD`, `TAAM_CODIGO_EMPAREJAMIENTO_TTL_HORAS`, `TAAM_CODIGO_LONGITUD`, `TAAM_PDF_MAX_MB`, `TAAM_QDRANT_COLLECTION`, `TAAM_CHUNK_SIZE`, `TAAM_CHUNK_OVERLAP`, `EMBEDDING_MODEL`, `INGESTA_REINTENTOS`, `INGESTA_BACKOFF_MAX_SEG`, `ALLOWED_ORIGINS`.

Opcional: `UAO_WORKSPACE_ROOT` apunta al directorio que contiene `data/` (por defecto se infiere como el padre de `proyecto-2/`).

## Estructura

```
src/api/              # FastAPI (salud, admin, staff/casos, telegram, webhook)
src/integracion/      # Telegram: cliente Bot API, manejador de updates (TASK-106)
src/agentes/          # LangChain create_agent, tools, PostgresSaver, HITL (TASK-103)
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

## Agente (TASK-103)

Módulo `src/agentes/`: ver [README del agente](src/agentes/README.md). Verificación rubrica: `./scripts/verificar_stack_m3.sh`.

Variables opcionales: `AGENTE_MODELO` (defecto `openai:gpt-4o-mini`), `AGENTE_RAG_K`.

## Próximas tareas Backlog
- **TASK-107** — recordatorios Telegram (UC-MVP-04) implementado
- **TASK-108+** — panel staff alertas, frontend React (TASK-109)

Casos de uso: [Caso de Uso TAAM](../backlog/docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md).
