# proyecto-2 — TAAM (Bot posoperatorio, Módulo 3)

Aplicación **independiente** del asistente M2 en [`proyecto-1/`](../proyecto-1/). Implementa el MVP **TAAM** según [decision-7](../backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md) (Ruta A LangChain, Telegram vía 2, `POST /chat`).

**Documentación de arquitectura (informe M3):** [doc-004 — Arquitectura TAAM](../backlog/docs/doc-004%20-%20Arquitectura-M3-Bot-Posoperatorio-TAAM.md) (diagramas, tabla M2 vs M3, matriz rubrica LangChain).

**Estudio OpenFang (Ruta B):** [doc-007 — Evaluacion OpenFang vs TAAM](../backlog/docs/doc-007%20-%20Evaluacion-OpenFang-Proyecto-2-TAAM.md) (viabilidad de migracion; recomendacion: mantener proyecto-2 en MVP).

**Milestone:** [m-0 — Agentic Final Project](../backlog/milestones/m-0%20-%20agentic-final-project.md).

## Relación con proyecto-1

| Tema | proyecto-1 (M2) | proyecto-2 (TAAM) |
|------|-----------------|-------------------|
| Agente | LangGraph + SSE | LangChain `create_agent` (TASK-103+) |
| API conversacional | `POST /api/agente/stream` | `POST /chat` (TASK-104) |
| Postgres OLTP | `app` en `:15432` (tablas `usuarios`, `config_admin_m2`, …) | Base **`taam`** en `:15433` (tablas `tipos_procedimiento`, `casos_postoperatorio`, `vinculos_telegram`, `alertas_triage`, …). **No compartir** `DATABASE_URL` con M2. |
| Qdrant | Instancias y colecciones M2 | Instancias y colección `taam_protocolos` dedicadas |
| Frontend | React en `proyecto-1/frontend/` | React nuevo en `proyecto-2/frontend/` (TASK-109) |
| Ingesta vectorial (Qdrant) | `data/markdown/` → colecciones `corpus_*` | Protocolos en `data/taam/procedimientos/` (subida admin) → `taam_protocolos` |
| Datos estructurados / prompts | Según M2 | FAQs: `data/structured/taam_faqs.json`; prompts: código en `src/agentes/` (sin Qdrant) |

**No** importar código de `proyecto-1` en runtime; solo compartir el workspace (`data/` en la raíz del repo) vía `src/rutas_workspace.py`.

## Datos y Qdrant (alcance)

En **proyecto-2** la única ingesta vectorial es la de **protocolos médicos** (PDF o Markdown) asociados a un `tipo_procedimiento`, subidos o reemplazados desde el panel o la API admin (`/api/admin/procedimientos`). Los chunks van a la colección `TAAM_QDRANT_COLLECTION` (defecto `taam_protocolos`) en una instancia Qdrant distinta de la de M2 (puerto host **6334** por defecto).

**No** se indexan en Qdrant:

- Prompts del agente (`src/agentes/prompts.py`, middleware `@dynamic_prompt` y contexto OLTP en runtime).
- FAQs postoperatorias (`data/structured/taam_faqs.json`; tool determinista, sin embeddings).
- Corpus institucional M2 (`data/markdown/`, colecciones `corpus_*` de `proyecto-1`).
- Historial conversacional, casos, vínculos Telegram, alertas de triage ni plantillas de recordatorios (Postgres OLTP o checkpointer).

La semilla demo con `--con-ingesta` o `TAAM_SEMBRAR_DEMO_CON_INGESTA=true` indexa solo el PDF de `COLE-LAP-001` en `data/taam/demo/`, no el corpus M2. No hay script `indexar_corpus_qdrant` en este proyecto.

## Requisitos

- Python **3.12.12** (exacto)
- [uv](https://docs.astral.sh/uv/)
- Docker y Docker Compose (recomendado para Postgres + Qdrant locales)
- Node.js **22** y **pnpm 11.1.1** si usará el panel React (`frontend/`)

## Guía paso a paso (desarrollo local)

Orden recomendado para dejar API, base de datos, vectores y usuarios demo listos. Los pasos 3–6 asumen Docker; si ejecuta la API con `uv run uvicorn` en el host, use los equivalentes indicados entre paréntesis.

### 1. Entrar al proyecto y copiar variables

```bash
cd proyecto-2
cp .env.example .env
```

Edite `.env` (no commitear). Mínimo para login staff y semillas:

| Variable | Valor sugerido (local) | Notas |
|----------|------------------------|-------|
| `STAFF_JWT_SECRET` | Cadena aleatoria ≥ 32 caracteres | Obligatoria; sin ella `POST /api/auth/staff/login` responde **503** |
| `STAFF_DEMO_ASISTENTE_PASSWORD` | `123456789` | Debe coincidir con la contraseña que usará en login y al sembrar |
| `STAFF_DEMO_CLINICO_PASSWORD` | `123456789` | Igual para los tres roles demo |
| `STAFF_DEMO_ADMIN_PASSWORD` | `123456789` | Igual para los tres roles demo |
| `ADMIN_API_KEY` | Clave larga local (opcional) | Alternativa a JWT para rutas `/api/admin/*` vía cabecera `X-Admin-Key` |
| `OPENAI_API_KEY` | Su clave | Necesaria para ingesta PDF → embeddings y agente en vivo |
| `QDRANT_URL` | `http://127.0.0.1:6334` | Con API en host; en Docker Compose la API usa `http://qdrant:6333` internamente |

Plantilla completa: [`.env.example`](.env.example).

### 2. Instalar dependencias Python

```bash
uv sync
```

### 3. Levantar infraestructura con Docker Compose

```bash
docker compose up --build -d
```

- El servicio **api** ejecuta **`alembic upgrade head`** al arrancar ([`scripts/docker_entrypoint.sh`](scripts/docker_entrypoint.sh)) y luego Uvicorn en el puerto **8001**.
- La semilla demo (`sembrar_demo_taam`) es **opt-in** con `TAAM_SEMBRAR_DEMO_HABILITADO=true` en `.env` (paso 5); por defecto no se ejecuta.
- Solo infra (sin API): `docker compose up -d postgres qdrant pgweb`.

Comprobar salud: `curl -sS http://127.0.0.1:8001/api/salud | jq .` → `"proyecto":"taam"`.

| Servicio | URL en el host (defecto) |
|----------|---------------------------|
| API | http://127.0.0.1:8001/api/salud |
| pgweb (Postgres) | http://127.0.0.1:8082 — usuario/contraseña/base = `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` (`postgres` / `postgres` / `taam`) |
| Qdrant dashboard | http://127.0.0.1:6334/dashboard |
| Qdrant REST | http://127.0.0.1:6334 |

Puertos TAAM vs M2: ver tabla en [Docker Compose](#docker-compose) más abajo.

### 4. Migraciones Alembic (si aplica)

| Escenario | Comando |
|-----------|---------|
| Stack con `docker compose up` (API en contenedor) | Ya aplicadas en el arranque del contenedor **api** |
| API en host + Postgres publicado en **15433** | `export DATABASE_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:15433/taam'` y `uv run alembic upgrade head` |
| Reaplicar en contenedor ya levantado | `docker compose exec api uv run alembic upgrade head` |

Revisiones en `alembic/versions/`: `0001_inicial_taam`, `0002_telegram_updates_procesados`, `0003_alertas_triage_auditoria`.

### 5. Usuarios y datos de prueba (semillas)

Tras migraciones y con `STAFF_JWT_SECRET` y las tres `STAFF_DEMO_*_PASSWORD` definidas en `.env`:

| Escenario | Qué hacer |
|-----------|-----------|
| Compose con semilla automática | En `.env`: `TAAM_SEMBRAR_DEMO_HABILITADO=true` (+ `OPENAI_API_KEY` si no desactivas ingesta; ver abajo). Tras `docker compose up`, el entrypoint ejecuta `sembrar_demo_taam`. |
| Compose sin semilla automática (default) | Dejar `TAAM_SEMBRAR_DEMO_HABILITADO=false` y usar los comandos manuales de esta sección. |
| Re-sembrar sin reiniciar | `docker compose exec api uv run python -m scripts.sembrar_demo_taam` (opcional `--con-ingesta`) |

**Variables de semilla en arranque Docker** (ver [`.env.example`](.env.example)):

- `TAAM_SEMBRAR_DEMO_HABILITADO` — `false` por defecto; `true` activa la semilla tras Alembic.
- `TAAM_SEMBRAR_DEMO_CON_INGESTA` — `true` por defecto cuando la semilla está activa: equivale a `--con-ingesta` (Qdrant + `OPENAI_API_KEY`). Poner `false` para sembrar sin indexar.

**Solo usuarios staff** (login JWT; sin casos ni PDF demo):

```bash
# Con API en Docker:
docker compose exec api uv run python -m scripts.sembrar_usuarios_staff_demo

# Con API en host:
uv run python -m scripts.sembrar_usuarios_staff_demo
```

**Demo completa** (usuarios + procedimiento `COLE-LAP-001` + casos `PAC-DEMO-001` / `PAC-DEMO-002` + alerta + código `DEMO2X` + hilo Telegram ficticio):

```bash
docker compose exec api uv run python -m scripts.sembrar_demo_taam
# Indexar PDF demo en Qdrant (por defecto si TAAM_SEMBRAR_DEMO_CON_INGESTA=true en entrypoint)
docker compose exec api uv run python -m scripts.sembrar_demo_taam --con-ingesta
```

Equivalente en `.env` para el arranque automático:

```env
TAAM_SEMBRAR_DEMO_HABILITADO=true
OPENAI_API_KEY=sk-...
# TAAM_SEMBRAR_DEMO_CON_INGESTA=false   # solo si no quieres ingesta al arrancar
```

La semilla es **idempotente**: puede repetirse; actualiza contraseñas si cambió las variables `STAFF_DEMO_*` en `.env`.

### 6. Qdrant — colección `taam_protocolos`

Única vía de ingesta vectorial en este proyecto (ver [Datos y Qdrant (alcance)](#datos-y-qdrant-alcance)).

- Colección dedicada M3: `TAAM_QDRANT_COLLECTION` (defecto `taam_protocolos`), **no** las colecciones `corpus_*` de M2.
- Tras subir un protocolo (PDF o Markdown) por API admin, la ingesta corre en segundo plano; estado en `indexacion_estado` del tipo de procedimiento.
- **CLI** (un UUID o todos los pendientes):

```bash
docker compose exec api uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid>
docker compose exec api uv run python -m scripts.ingestar_protocolo_pdf --todos-pendientes
```

En host: mismos comandos con `uv run` y `QDRANT_URL=http://127.0.0.1:6334`.

### 7. Panel React (opcional)

```bash
cd frontend
pnpm install
pnpm dev
```

Abrir http://127.0.0.1:5174/login con cualquier usuario de la tabla siguiente. Detalle de rutas: [`frontend/README.md`](frontend/README.md).

### 8. Verificar login staff

```bash
curl -sS -X POST http://127.0.0.1:8001/api/auth/staff/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"asistente@demo.taam","password":"123456789"}' | jq .
```

Debe devolver `access_token` y `rol`. Si falla con 401, vuelva a ejecutar la semilla (paso 5) tras alinear `.env` y contraseñas.

---

## Usuarios de prueba (staff demo)

Creados por `scripts/sembrar_usuarios_staff_demo.py` (o incluidos en `scripts/sembrar_demo_taam.py`). La contraseña en login es la que tenga en `.env` en el momento de sembrar; en entorno local del curso se usa **`123456789`** para los tres.

| Email | Contraseña (login) | Rol | Nombre en sistema | Función en TAAM |
|-------|-------------------|-----|-------------------|-----------------|
| `asistente@demo.taam` | `123456789` | `asistente` | Asistente Demo | Registro de casos postoperatorio, generación de código de emparejamiento Telegram (`/casos` en el panel). En API de seguimiento ve **PII enmascarada** (solo últimos 4 caracteres de doc. paciente y `chat_id`). |
| `clinico@demo.taam` | `123456789` | `clinico` | Clinico Demo | Bandeja de alertas de triage, revisión de conversaciones del bot y resumen del caso (`/seguimiento`). Ve identificadores completos del paciente y Telegram. |
| `admin@demo.taam` | `123456789` | `admin` | Admin Demo | Catálogo de tipos de procedimiento y PDF (`/admin/procedimientos`), reindexación Qdrant y rutas `/api/admin/*` con JWT `rol=admin` o `X-Admin-Key`. También puede usar rutas staff como los demás roles. |

Variables que alimentan la semilla (deben coincidir con la contraseña de la tabla):

```env
STAFF_DEMO_ASISTENTE_PASSWORD=123456789
STAFF_DEMO_CLINICO_PASSWORD=123456789
STAFF_DEMO_ADMIN_PASSWORD=123456789
```

**Datos demo adicionales** (solo tras `sembrar_demo_taam`):

| Recurso | Valor | Uso |
|---------|-------|-----|
| Procedimiento | `COLE-LAP-001` — Colecistectomía laparoscópica (demo) | Select al crear caso; PDF en `data/taam/demo/` |
| Caso A | `PAC-DEMO-001` — Ana Ficticia Lopez | Vinculado a `chat_id` **ficticio** `111111111` (solo panel/seguimiento); alerta **urgente** pendiente; hilo sembrado. Para Telegram real, empareje con `/start` y un `chat_id` válido |
| Caso B | `PAC-DEMO-002` — Bruno Ficticio Ruiz | Código de emparejamiento **`DEMO2X`** (TTL 24 h) para probar `/start DEMO2X` en Telegram (`222222222` es placeholder hasta emparejar) |
| Cirujano ficticio | `DOC-DEMO-001` / Dr. Demo TAAM | Metadatos del caso |

**FAQs estructuradas** (tool del agente): `data/structured/taam_faqs.json`. Búsqueda determinista en JSON; **no** se embeden en Qdrant.

---

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
| `POST` | `/api/admin/procedimientos` | Multipart: `metadata` (JSON `codigo`, `nombre`) + `archivo` (PDF `.pdf` o Markdown `.md`) |
| `GET` | `/api/admin/procedimientos` | Listado (`limit`, `offset`); incluye `formato_protocolo` (`pdf` \| `markdown`) |
| `GET` | `/api/admin/procedimientos/{id}` | Detalle |
| `PATCH` | `/api/admin/procedimientos/{id}` | Actualizar metadata y/o reemplazar protocolo (PDF ↔ Markdown) |
| `POST` | `/api/admin/procedimientos/{id}/reindexar` | Relanza ingesta Qdrant (202) |

Cada procedimiento tiene **un solo archivo activo** en disco:

- PDF: `data/taam/procedimientos/{uuid}/protocolo.pdf`
- Markdown: `data/taam/procedimientos/{uuid}/protocolo.md`

(Volumen Docker montado en `/app/data/taam`.) Tamaño máximo por defecto: **10 MB** (`TAAM_PDF_MAX_MB`; aplica a PDF y Markdown). Tras subir o reemplazar, la API encola ingesta en segundo plano; `indexacion_estado` pasa a `ok` o `error` cuando termina.

Migración **`0004_formato_protocolo_taam`**: columna `formato_protocolo` (default `pdf` para filas existentes). Aplicar con `alembic upgrade head` en host o `docker compose exec api uv run alembic upgrade head`.

### Catálogo de médicos (admin)

Rutas bajo `/api/admin/medicos`. Misma autenticación que procedimientos: **`X-Admin-Key`** o JWT staff con `rol=admin`. Sin Qdrant ni archivos; solo metadatos en Postgres (`medicos`).

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/admin/medicos` | JSON: `codigo_registro`, `nombre_completo`, `especialidad` (opcional) → 201 |
| `GET` | `/api/admin/medicos` | Listado paginado `{ items, total }`; query `limit`, `offset`, `activo` (opcional) |
| `GET` | `/api/admin/medicos/{id}` | Detalle por UUID |
| `PATCH` | `/api/admin/medicos/{id}` | JSON parcial; 409 si `codigo_registro` duplicado |
| `DELETE` | `/api/admin/medicos/{id}` | Baja lógica (`activo=false`); 409 si hay caso **activo** con `cirujano_id` = `codigo_registro` |

`codigo_registro` es ASCII `[A-Za-z0-9._-]+` (alineado con `cirujano_id` en casos). La semilla demo crea `DOC-DEMO-001` / Dr. Demo TAAM.

Migración **`0005_medicos`**: tabla `medicos`. Aplicar con `alembic upgrade head`.

```bash
export ADMIN_API_KEY='cambiar-por-clave-segura'

curl -sS -H "X-Admin-Key: $ADMIN_API_KEY" -H "Content-Type: application/json" \
  -d '{"codigo_registro":"DOC-001","nombre_completo":"Dra. Ejemplo","especialidad":"Cirugia"}' \
  http://127.0.0.1:8001/api/admin/medicos | jq .

curl -sS -H "X-Admin-Key: $ADMIN_API_KEY" \
  "http://127.0.0.1:8001/api/admin/medicos?limit=20&activo=true" | jq .
```

### Ingesta protocolo → Qdrant (`taam_protocolos`)

Única vía de ingesta vectorial en TAAM; no aplica a prompts, FAQs ni `data/markdown/` de M2.

- **Stack:** `pdfplumber` (PDF) o lectura UTF-8 con front matter YAML opcional (Markdown) + `RecursiveCharacterTextSplitter` (800 / 120) + `OpenAIEmbeddings` + `langchain_qdrant.QdrantVectorStore`.
- **Colección dedicada** (no `corpus_*` de M2): `TAAM_QDRANT_COLLECTION` (default `taam_protocolos`), REST en host **6334**.
- **CLI:** `uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid>` o `--todos-pendientes` (acepta ambos formatos según `formato_protocolo` en BD).
- **Limitación:** PDF escaneado sin OCR o Markdown con cuerpo vacío tras el front matter → `indexacion_estado=error`.

Ejemplos locales:

```bash
export ADMIN_API_KEY='cambiar-por-clave-segura'

# PDF
curl -sS -H "X-Admin-Key: $ADMIN_API_KEY" \
  -F 'metadata={"codigo":"cole-lap","nombre":"Colecistectomia laparoscopica"};type=application/json' \
  -F "archivo=@protocolo.pdf;type=application/pdf" \
  http://127.0.0.1:8001/api/admin/procedimientos | jq .

# Markdown
curl -sS -H "X-Admin-Key: $ADMIN_API_KEY" \
  -F 'metadata={"codigo":"cole-lap-md","nombre":"Colecistectomia (MD)"};type=application/json' \
  -F "archivo=@protocolo.md;type=text/markdown" \
  http://127.0.0.1:8001/api/admin/procedimientos | jq .
```

### Autenticación staff (JWT, TASK-105)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/auth/staff/login` | Body JSON `email`, `password` → `access_token` (JWT HS256, 8 h por defecto) |

Variables: `STAFF_JWT_SECRET` (obligatoria para auth staff), `STAFF_JWT_EXPIRE_HORAS` (opcional). Contraseñas demo: `STAFF_DEMO_*_PASSWORD` (ver [Usuarios de prueba](#usuarios-de-prueba-staff-demo) y [guía paso a paso](#guía-paso-a-paso-desarrollo-local)).

```bash
TOKEN=$(curl -sS -X POST http://127.0.0.1:8001/api/auth/staff/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"clinico@demo.taam","password":"123456789"}' | jq -r .access_token)

curl -sS -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8001/api/staff/casos | jq .
```

**Rate limit** en login: no implementado en MVP; en producción conviene limitar en proxy (nginx/Cloudflare).

`STAFF_API_KEY` / `X-Staff-Key` quedaron **deprecados**; el panel React (**TASK-112**) usará Bearer JWT en memoria de pestaña.

### Casos postoperatorio y emparejamiento Telegram (UC-MVP-02)

Rutas staff bajo `/api/staff/casos` (cabecera **`Authorization: Bearer`**). El emparejamiento lo invoca el webhook Telegram (**TASK-106**) con **`X-Telegram-Bot-Api-Secret-Token`** = `TELEGRAM_WEBHOOK_SECRET`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/staff/tipos-procedimiento` | Tipos con `indexacion_estado=ok` (`id`, `codigo`, `nombre`) para select de alta |
| `GET` | `/api/staff/medicos` | Medicos activos del catalogo (`codigo_registro`, `nombre_completo`, `especialidad`) para select de cirujano; `limit` 1–100 (default 100) |
| `POST` | `/api/staff/casos` | Alta de caso (`estado=activo`); exige `tipo_procedimiento` con `indexacion_estado=ok` y par `cirujano_id`/`cirujano_nombre` alineado con el catalogo |
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
| `POST` | `/api/staff/casos/{id}/reanudar-hitl` | Body `{ "decision": "approve" \| "reject" }`; cierra interrupción HITL en `escalar_a_equipo` (`reanudado: false` si no había pendiente) |

Si el paciente escribe de nuevo en Telegram tras un escalamiento sin aprobación staff, el backend reanuda el hilo con `reject` automáticamente antes del turno (evita error OpenAI por `tool_call` huérfano). Ver [`src/agentes/README.md`](src/agentes/README.md).

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

Job interno (asyncio en el lifespan de FastAPI): cada `RECORDATORIOS_JOB_INTERVAL_SEG` (default 60) busca pendientes con `programado_at <= now()` y envía por la misma Bot API que TASK-106. Si el caso no tiene vínculo Telegram, omite y registra log. Los `chat_id` de semilla demo (`111111111`, `222222222`) **no** se envían a Telegram (evita `400 chat not found` en Docker local).

Variables (ver también `.env.example`):

- `RECORDATORIOS_JOB_HABILITADO` — `true`/`false`; en tests y en Compose por defecto `false` salvo que lo active en `.env`.
- `RECORDATORIOS_JOB_INTERVAL_SEG` — intervalo del job en segundos.

Si un `TELEGRAM_BOT_TOKEN` real quedó expuesto en logs (p. ej. traceback con URL del bot), revóquelo en @BotFather y actualice `.env`.

Placeholders en `texto_plantilla`: `{nombre_paciente}`, `{tipo_procedimiento}`, `{texto_cuidado}`.

## Docker Compose

Resumen de servicios; el flujo completo (`.env`, semillas, Qdrant, usuarios) está en [Guía paso a paso](#guía-paso-a-paso-desarrollo-local).

```bash
cd proyecto-2
docker compose up --build -d    # recomendado en segundo plano
# docker compose up --build   # primer arranque en primer plano (logs)
```

El contenedor **api** ejecuta `alembic upgrade head` al arrancar ([`scripts/docker_entrypoint.sh`](scripts/docker_entrypoint.sh)) y luego Uvicorn. Opcionalmente ejecuta `sembrar_demo_taam` si `TAAM_SEMBRAR_DEMO_HABILITADO=true` (paso 5). **No** ejecuta `sembrar_usuarios_staff_demo` por separado (la demo completa ya incluye usuarios staff).

El servicio **api** carga [`proyecto-2/.env`](.env) vía `env_file` en `docker-compose.yml` (incluye `STAFF_JWT_SECRET` y `STAFF_DEMO_*_PASSWORD`). Sin `STAFF_JWT_SECRET`, `POST /api/auth/staff/login` responde **503**.

### Puertos por defecto (coexistencia con M2)

| Servicio | proyecto-1 (M2) | proyecto-2 (TAAM) |
|----------|-----------------|-------------------|
| API HTTP | 8000 | **8001** |
| Postgres (host) | 15432 | **15433** |
| Qdrant REST (host) | 6333 | **6334** |
| Qdrant gRPC (host) | 6334 | **6335** |
| pgweb (host) | 8081 | **8082** |
| Vite (dev) | 5173 | **5174** (previsto) |

### URLs en el navegador (host TAAM)

Tras `docker compose up`, abre estas direcciones desde tu máquina (usa `127.0.0.1` o `localhost`; **no** `0.0.0.0`):

| Servicio | URL |
|----------|-----|
| API (salud) | http://127.0.0.1:8001/api/salud |
| pgweb (Postgres) | http://127.0.0.1:8082 |
| Qdrant (dashboard) | http://127.0.0.1:6334/dashboard |
| Qdrant (REST) | http://127.0.0.1:6334 |

**Credenciales pgweb:** las mismas que `POSTGRES_USER`, `POSTGRES_PASSWORD` y base `POSTGRES_DB` (`taam` por defecto) del `.env`.

**Logs engañosos de los contenedores:** pgweb y Qdrant imprimen URLs internas al arrancar (`http://0.0.0.0:8081/` y `http://localhost:6333/dashboard`). Esos puertos son los del **contenedor**, no los publicados en el host TAAM. Usa siempre la tabla de arriba (8082 y 6334 por defecto).

- **Solo infraestructura:** `docker compose up -d postgres qdrant pgweb` (sin API).

Si algún puerto está ocupado, sobreescribir en `.env` (`API_PORT`, `POSTGRES_PUBLISH_PORT`, `QDRANT_REST_PORT`, `PGWEB_PUBLISH_PORT`, etc.).

API **fuera de Docker** con Postgres en el host: ver pasos 4–5 de la [guía paso a paso](#guía-paso-a-paso-desarrollo-local).

El healthcheck del contenedor **api** solo valida `GET /api/salud`; no ejecuta Alembic ni semillas por sí solo.

## Variables de entorno

Plantilla: [`.env.example`](.env.example). Base de datos: `DATABASE_URL` (compose suele usar `postgres://…`; el backend lo normaliza a `postgresql+asyncpg://` y quita parámetros de query como `sslmode`, que asyncpg no admite) o bien `POSTGRES_HOST`, `POSTGRES_PORT` (defecto **15433**), `POSTGRES_DB` (`taam`), `POSTGRES_USER`, `POSTGRES_PASSWORD`.

Otras variables M3: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `QDRANT_URL`, `OPENAI_API_KEY`, `AGENTE_MODELO`, `AGENTE_RAG_K`, `ADMIN_API_KEY`, `STAFF_JWT_SECRET`, `STAFF_JWT_EXPIRE_HORAS`, `STAFF_DEMO_*_PASSWORD`, `TAAM_CODIGO_EMPAREJAMIENTO_TTL_HORAS`, `TAAM_CODIGO_LONGITUD`, `TAAM_PDF_MAX_MB`, `TAAM_QDRANT_COLLECTION`, `TAAM_CHUNK_SIZE`, `TAAM_CHUNK_OVERLAP`, `EMBEDDING_MODEL`, `INGESTA_REINTENTOS`, `INGESTA_BACKOFF_MAX_SEG`, `ALLOWED_ORIGINS`.

Opcional: `UAO_WORKSPACE_ROOT` apunta al directorio que contiene `data/` (por defecto se infiere como el padre de `proyecto-2/`).

## Estructura

```
src/api/              # FastAPI (salud, admin, staff/casos, telegram, webhook)
src/integracion/      # Telegram: cliente Bot API, manejador de updates (TASK-106)
src/agentes/          # LangChain create_agent, tools, AsyncPostgresSaver, HITL (TASK-103)
src/ingesta/          # ingesta protocolo PDF o Markdown → Qdrant (LangChain)
src/rag/              # vector store TAAM
src/persistencia/     # modelos SQLAlchemy, motor async, repositorios (TASK-99)
src/configuracion.py
src/rutas_workspace.py
alembic/versions/     # migraciones OLTP TAAM
frontend/             # placeholder hasta TASK-109
scripts/              # `ingestar_protocolo_pdf.py`, demo (TASK-114)
tests/                # API, ingesta, persistencia (ver tests/README.md)
```

## Pruebas automatizadas

```bash
cd proyecto-2
uv run pytest
```

Guía de marcadores, mocks y Postgres opcional: [tests/README.md](tests/README.md). La suite por defecto no requiere `TELEGRAM_BOT_TOKEN` ni OpenAI real.

## Agente (TASK-103)

Módulo `src/agentes/`: ver [README del agente](src/agentes/README.md). Verificación rubrica: `./scripts/verificar_stack_m3.sh`.

Variables opcionales: `AGENTE_MODELO` (defecto `openai:gpt-4o-mini`), `AGENTE_RAG_K`.

## Demo en vivo (TASK-114)

Guion minuto a minuto: [GUION-DEMO-TAAM.md](../backlog/docs/usecases/GUION-DEMO-TAAM.md). Datos ficticios alineados al [caso de uso TAAM](../backlog/docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md) (secciones 9–10).

**Preparación:** seguir la [guía paso a paso](#guía-paso-a-paso-desarrollo-local) hasta el paso 5 con `sembrar_demo_taam` (y `--con-ingesta` si necesita RAG en vivo). Login panel: usuarios de [Usuarios de prueba](#usuarios-de-prueba-staff-demo) (`123456789`); flujo clínico típico con `clinico@demo.taam` y caso `PAC-DEMO-001`.

**Telegram:** registrar webhook HTTPS (`scripts/configurar_webhook_telegram.py`). Caso B: `/start DEMO2X`. En **tests**, el agente se mockea; en demo en vivo use API real según `.env`.

**Frontend:** `cd frontend && pnpm dev` → http://127.0.0.1:5174/login .

## Próximas tareas Backlog
- **TASK-107** — recordatorios Telegram (UC-MVP-04) implementado
- **TASK-108+** — panel staff alertas, frontend React (TASK-109)

Casos de uso: [Caso de Uso TAAM](../backlog/docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md).
