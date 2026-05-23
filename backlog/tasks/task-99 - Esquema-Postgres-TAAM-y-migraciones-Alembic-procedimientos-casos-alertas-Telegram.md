---
id: TASK-99
title: >-
  Esquema Postgres TAAM y migraciones Alembic (procedimientos, casos, alertas,
  Telegram)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:15'
updated_date: '2026-05-21 23:04'
labels:
  - modulo-3
  - taam
  - postgres
  - alembic
milestone: m-0
dependencies:
  - TASK-98
references:
  - proyecto-1/src/persistencia/modelos.py
  - proyecto-1/alembic/
  - >-
    backlog/decisions/decision-7 -
    Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - proyecto-2/docker-compose.yml
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

TAAM (Módulo 3, `proyecto-2/`) necesita un **OLTP PostgreSQL dedicado**, distinto del de M2 en `proyecto-1/` ([decision-7](backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md)). Sin tablas acordadas, las tareas de API (TASK-100–102), agente (TASK-103) y panel staff (TASK-108) no comparten el mismo modelo de procedimientos, casos, vínculo Telegram ni alertas de triage.

**Dependencia:** TASK-98 (scaffold FastAPI + compose con Postgres `:15433`).

**Referencias de patrón (no importar en runtime):** `proyecto-1/src/persistencia/modelos.py`, `proyecto-1/alembic/`.

## Objetivo

Entregar el **esquema inicial TAAM** con SQLAlchemy 2 async, migración Alembic `0001_inicial_taam`, motor/sesión reutilizable y repositorios CRUD mínimos para las entidades que desbloquean UC-MVP-01..05.

## Tablas (nombres físicos en Postgres)

| Tabla | Propósito | Campos clave |
|-------|-----------|--------------|
| `tipos_procedimiento` | Catálogo UC-MVP-01 | `codigo` (unique), `nombre`, `ruta_pdf`, `hash_pdf`, `indexacion_estado` (`pendiente`\|`ok`\|`error`), `qdrant_collection_version`, `created_at` |
| `casos_postoperatorio` | Caso quirúrgico UC-MVP-02 | FK → `tipos_procedimiento`, `paciente_doc_id`, `paciente_nombre`, `cirujano_id`, `cirujano_nombre`, `fecha_cirugia`, `notas_especificas`, `estado` (`activo`\|`cerrado`), índice `(paciente_doc_id, estado)` |
| `vinculos_telegram` | Emparejamiento UC-MVP-02 | FK → `casos_postoperatorio`, `telegram_chat_id` (**unique**), `codigo_emparejamiento`, `codigo_expira_at`, `vinculado_at` |
| `alertas_triage` | Bandeja UC-MVP-05 | FK → `casos_postoperatorio`, `severidad` (`info`\|`seguimiento`\|`urgente`), `resumen`, `mensaje_paciente_ref`, `tool_trace_json`, `revisado`, `revisado_at`, `created_at` |
| `plantillas_recordatorio` | UC-MVP-04 (cron) | FK → `tipos_procedimiento`, `tipo` (`medicacion`\|`terapia`\|`control`), `offset_horas_desde_cirugia`, `texto_plantilla` |
| `recordatorios_enviados` | Trazabilidad envíos | FK → `casos_postoperatorio` + `plantillas_recordatorio`, `programado_at`, `enviado_at`, `estado` |
| `usuarios_staff` | Auth panel TASK-110 | `email` (unique), `nombre`, `rol` (`asistente`\|`clinico`\|`admin`), `hash_credencial` |

## Reglas de diseño

- **BD separada de M2:** `DATABASE_URL` / compose TAAM en puerto host **15433**; no reutilizar tablas `usuarios` ni `chat_history` de M2.
- **Identificadores Python:** español ASCII (`caso_postoperatorio`, `vinculo_telegram`); sin tildes ni `ñ` en nombres de símbolos.
- **PII:** `paciente_doc_id`, `paciente_nombre`, `mensaje_paciente_ref` — documentar en migración/README que la API staff debe enmascarar en listados (TASK-108).
- **Checkpointer LangChain:** tablas de `PostgresSaver` **no** van en esta migración; `session_id` = `telegram:{chat_id}` según decision-7.
- **Convención Alembic:** revisión `0001_inicial_taam`; extensión `pgcrypto` + `gen_random_uuid()` en PKs UUID.

## Entregables

- `proyecto-2/alembic.ini`, `proyecto-2/alembic/env.py`, `proyecto-2/alembic/versions/0001_inicial_taam.py`
- `proyecto-2/src/persistencia/modelos.py`, `motor.py`, `repositorios/*.py`
- `proyecto-2/tests/persistencia/` (SQLite async + integración Postgres opcional)
- README `proyecto-2/` — sección BD y comando `uv run alembic upgrade head`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 `uv run alembic upgrade head` en Postgres TAAM vacío (compose :15433 o `INTEGRATION_POSTGRES_ASYNC_URL`) crea las siete tablas sin error
- [x] #2 #2 Modelos SQLAlchemy 2 en `src/persistencia/modelos.py` reflejan las tablas anteriores con type hints y relaciones FK declaradas
- [x] #3 #3 Repositorios async exponen CRUD mínimo: crear/listar `TipoProcedimiento`, crear/listar `CasoPostoperatorio`, crear/obtener por `telegram_chat_id` en `VinculoTelegram`, crear/listar `AlertaTriage`
- [x] #4 #4 Tests en `tests/persistencia/`: (a) SQLite in-memory validan FK `casos_postoperatorio`→`tipos_procedimiento` y unicidad de `telegram_chat_id`; (b) test marcado `integration_postgres` valida migración Alembic en Postgres real
- [x] #5 #5 `proyecto-2/README.md` documenta separación OLTP respecto a M2, variables `DATABASE_URL`/`POSTGRES_*` y flujo `alembic upgrade head` antes de levantar APIs que usen BD
- [x] #6 #6 `src/configuracion.py` expone `url_base_datos_async()` normalizando `postgres://` y `postgresql+asyncpg://` desde `.env`
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Dependencias:** desde `proyecto-2/`, `uv add sqlalchemy[asyncio] asyncpg psycopg[binary] alembic`; marcar `integration_postgres` en `pyproject.toml`.
2. **Configuración:** extender `src/configuracion.py` con `POSTGRES_*`, `url_base_datos_async()` / `url_base_datos_sync()` (normalizar `postgres://` del compose).
3. **Modelos:** `src/persistencia/modelos.py` — `Base` + siete tablas, enums como `String` con `CheckConstraint` o constantes documentadas.
4. **Alembic:** copiar patrón `proyecto-1/alembic/env.py` apuntando a `src.configuracion` y `Base.metadata`; generar `0001_inicial_taam.py` con índices y FKs.
5. **Motor:** `src/persistencia/motor.py` — `crear_motor_async`, `crear_session_factory`, `obtener_sesion_db` (para routers posteriores).
6. **Repositorios:** `tipos_procedimiento`, `casos_postoperatorio`, `vinculos_telegram`, `alertas_triage` con métodos `crear`, `listar` (paginación simple), búsquedas por id/chat_id.
7. **Tests:** fixture SQLite `sqlite+aiosqlite:///:memory:` con `create_all`; test integración opcional con `EJECUTAR_INTEGRACION_POSTGRES=1` y puerto 15433.
8. **Docs:** actualizar README y comentario en compose; ejecutar `uv run pytest` y marcar AC.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- `indexacion_estado` en `tipos_procedimiento` desbloquea validación TASK-102 (`ok` antes de activar caso).
- `codigo_expira_at` en `vinculos_telegram` prepara TTL 24h de TASK-102 sin cambiar esquema después.
- Repositorios **no** deben importarse desde routers hasta TASK-100+; solo tests y futuro `Depends`.
- Compose TAAM: tras esta tarea, documentar migración manual `docker compose exec api uv run alembic upgrade head` (servicio `db-init` opcional en tarea futura).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Esquema OLTP TAAM en proyecto-2: siete tablas (tipos_procedimiento, casos_postoperatorio, vinculos_telegram, alertas_triage, plantillas_recordatorio, recordatorios_enviados, usuarios_staff), migración Alembic 0001_inicial_taam, modelos SQLAlchemy 2 async, motor/sesión y cuatro repositorios CRUD. Configuración con url_base_datos_async/sync y normalización postgres://. Tests: SQLite (FK + unicidad telegram_chat_id) y integración Postgres opcional. README y Dockerfile actualizados con flujo alembic upgrade head.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Dependencias SQLAlchemy/Alembic/psycopg/asyncpg añadidas con `uv add` y `uv.lock` actualizado
- [x] #2 `uv run pytest` en `proyecto-2/` pasa (tests de integración Postgres se omiten sin `EJECUTAR_INTEGRACION_POSTGRES=1`)
- [x] #3 Comentario en migración `0001` lista campos PII a enmascarar en API staff
- [x] #4 Sin secretos ni credenciales reales en código ni en notas de tarea
<!-- DOD:END -->
