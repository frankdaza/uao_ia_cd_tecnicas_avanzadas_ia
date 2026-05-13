---
id: TASK-46
title: Esquema de base de datos y migración Alembic inicial (tabla usuarios)
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-13 00:58'
labels:
  - postgres
  - alembic
  - sqlalchemy
  - modulo-2
dependencies:
  - TASK-44
  - TASK-45
references:
  - alembic/
  - src/persistencia/modelos.py
  - src/api/configuracion.py
documentation:
  - .claude/skills/uv-python-env/SKILL.md
priority: high
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Se necesita persistir usuarios identificados por **documento de identidad** único y **nombre**, con auditoría básica de creación y último acceso. El historial de chat en formato LangChain (`chat_history`) será creado por **`PostgresChatMessageHistory.create_tables`** en runtime (task-48); esta task cubre solo el esquema **aplicación** vía Alembic.

## Objetivo

1. Inicializar proyecto **Alembic** en `alembic/` (`env.py`, `script.py.mako`, `versions/`).
2. Definir modelo SQLAlchemy 2.x **`Usuario`** en `src/persistencia/modelos.py`:
   - `id` UUID PK (default generado en DB o en app, documentar).
   - `documento_identidad` **único**, indexado.
   - `nombre` (texto).
   - `created_at`, `updated_at`, `last_login_at` (timestamps con timezone).
3. Configurar `alembic/env.py` para leer `DATABASE_URL` desde **pydantic-settings** (misma fuente que la app).
4. Generar revisión inicial `0001_create_usuarios.py` que crea la tabla `usuarios` (o nombre acordado en español ASCII: `usuarios`).

## Tests

Preferir `pytest` con **testcontainers** o `pytest-postgresql` si el esfuerzo es razonable; si no, smoke test documentado contra contenedor Compose y marcador `integration_postgres` para skips en CI sin Docker.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Directorio `alembic/` versionado con configuración funcional
- [x] #2 Modelo `Usuario` reflejado en migración y en metadata SQLAlchemy
- [x] #3 `alembic upgrade head` crea la tabla esperada en Postgres limpio
- [x] #4 Restricción UNIQUE en `documento_identidad` y índice verificable
- [x] #5 `env.py` no imprime secretos; usa URL desde settings
- [x] #6 Documentación en cuerpo de task o README: tabla `chat_history` la crea LangChain en lifespan (no Alembic)
- [x] #7 Al menos un test automatizado o script de verificación reproducible
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. `alembic init` adaptado al layout del repo (import string `src.persistencia.modelos`).
2. Implementar `Usuario` con tipos `Mapped` / `mapped_column` (SQLAlchemy 2).
3. Autogenerate o escribir a mano migración inicial revisada.
4. Cablear `DATABASE_URL` async vs sync: Alembic suele usar URL sync (`postgresql+psycopg://`); documentar dual URL si hace falta.
5. Añadir test o job CI opcional con servicio Postgres.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Convención de nombres de tabla en español ASCII (`usuarios`) alineada a rules del proyecto.
- Si la app usa async engine, mantener clara separación entre URL sync para migraciones y async para runtime.

Verificacion local recomendada: docker compose up -d postgres y ALEMBIC_SYNC_DATABASE_URL o DATABASE_URL alineados con credenciales del volumen; uv run alembic upgrade head.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agrego el modelo SQLAlchemy 2.x Usuario en src/persistencia/modelos.py (id UUID con gen_random_uuid() en servidor, documento_identidad unico, nombre, timestamps con zona y last_login_at). Alembic usa target_metadata = Base.metadata y la misma fuente de URL que la app (pydantic-settings en alembic/env.py, override ALEMBIC_SYNC_DATABASE_URL para driver sincrono psycopg). Migracion inicial alembic/versions/0001_create_usuarios.py crea la tabla usuarios con restriccion uq_usuarios_documento_identidad. Pruebas: tests/persistencia/test_modelo_usuario.py (unitarias) y test de integracion con marcador integration_postgres (variable INTEGRATION_POSTGRES_ASYNC_URL y skip ante OperationalError). README documenta que chat_history la crea LangChain en lifespan, no Alembic. Se elimino la revision base vacia 20260512_0001 y se anadio path_separator=os en alembic.ini.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run alembic upgrade head` funciona contra Postgres del compose
- [x] #2 `uv run pytest` verde para tests nuevos o marcados skip explícito
- [x] #3 `ruff check` en módulos nuevos
<!-- DOD:END -->
