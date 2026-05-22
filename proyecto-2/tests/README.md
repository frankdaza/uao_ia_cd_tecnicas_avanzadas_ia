# Pruebas TAAM (`proyecto-2/tests`)

Suite **pytest** del Módulo 3. Por defecto corre **sin Docker**, **sin Telegram real** y **sin OpenAI** en el camino caliente (agente e ingesta mockeados donde aplica).

## Comando canónico (CI local)

```bash
cd proyecto-2
uv sync
uv run pytest
```

Equivalente explícito (excluye solo los que hacen `skip` sin env):

```bash
uv run pytest -q
```

Salida esperada: decenas de tests en verde; **2 skipped** (`integration_postgres` sin `EJECUTAR_INTEGRACION_POSTGRES=1`).

## Tipos de prueba

| Tipo | Ubicación típica | Requiere Docker / red | Marcador |
|------|------------------|------------------------|----------|
| **Unit / API** | `tests/api/`, `tests/agentes/`, `tests/ingesta/`, `tests/structured/` | No | (ninguno) |
| **Persistencia SQLite** | `tests/persistencia/test_repositorios_taam_sqlite.py` | No | — |
| **Integración Postgres** | `tests/persistencia/test_migracion_taam_postgres.py`, `tests/agentes/test_checkpointer_postgres.py` | Sí (Postgres TAAM `:15433`) | `@pytest.mark.integration_postgres` |
| **Regresión M3** | `tests/integracion/test_aislamiento_m3.py` | No | — |

> **Nota:** el marcador del repo es `integration_postgres`, no `integration` genérico. Los tests marcados hacen `pytest.skip` salvo que definas:

```bash
export EJECUTAR_INTEGRACION_POSTGRES=1
export INTEGRATION_POSTGRES_ASYNC_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:15433/taam'
uv run pytest -m integration_postgres
```

Levanta Postgres con `docker compose up -d` desde `proyecto-2/` antes de esa corrida.

## Variables de entorno en tests

| Variable | Uso en tests |
|----------|----------------|
| `UAO_WORKSPACE_ROOT` | Fixture `workspace_tmp` (PDFs/FAQs aislados) |
| `TELEGRAM_WEBHOOK_SECRET` | Fixture `secreto_telegram` → valor fijo de prueba |
| `STAFF_JWT_SECRET`, `STAFF_DEMO_*_PASSWORD` | Login staff en API tests |
| `ADMIN_API_KEY` | Cabecera admin |
| `RECORDATORIOS_JOB_HABILITADO` | Autouse `false` en `tests/api/conftest.py` |
| `OPENAI_API_KEY` | Solo ingesta: `sk-test-falso` vía monkeypatch |

**No** se necesita `TELEGRAM_BOT_TOKEN` para que pase la suite por defecto: el cliente Telegram se parchea con `mensajes_telegram_enviados` en `test_telegram_webhook.py`.

## Fixtures principales (`tests/api/conftest.py`)

- `app_api` — FastAPI + SQLite en memoria + lifespan.
- `cliente_api` — `httpx.AsyncClient` ASGI.
- `cabecera_staff` / `cabecera_telegram` / `cabecera_admin` — auth de prueba.
- `mensajes_telegram_enviados` — captura envíos mock (ver `test_telegram_webhook.py`).

Agente (tools sin LLM): `tests/agentes/conftest.py` — `caso_vinculado_telegram_123`, `contexto_agente_123`.

## Matriz UC → archivos

| Capacidad | Archivo |
|-----------|---------|
| `POST /chat` | `api/test_chat.py` |
| Webhook Telegram | `api/test_telegram_webhook.py` |
| Alertas staff | `api/test_staff_seguimiento.py` |
| Tool triage → `alertas_triage` | `agentes/test_tools_oltp.py` |
| Ingesta PDF / idempotencia | `ingesta/test_protocolo_pdf.py` |
| FAQs JSON Schema | `structured/test_taam_faqs_json_schema.py` |
| Aislamiento vs M2 | `integracion/test_aislamiento_m3.py` |

## Mocks habituales

- **Agente:** `monkeypatch.setattr("src.api.servicios.chat.invocar_agente", ...)` devuelve `AIMessage` sin API.
- **Telegram:** parche de `ClienteTelegram.enviar_mensaje`.
- **Qdrant:** `QdrantClient(":memory:")` en tests de ingesta.

## Regresión M3 (coexistencia con `proyecto-1`)

Los tests de `integracion/test_aislamiento_m3.py` verifican que el código TAAM no importa paquetes de M2 y que `GET /api/salud` identifica `proyecto: "taam"`. Bases y puertos TAAM (8001, 15433, 6334) están en `docker-compose.yml` y no deben mezclarse con los de M2 (8000, 15432, 6333).

## Depuración

```bash
uv run pytest tests/api/test_chat.py -v
uv run pytest -k telegram --tb=short
```
