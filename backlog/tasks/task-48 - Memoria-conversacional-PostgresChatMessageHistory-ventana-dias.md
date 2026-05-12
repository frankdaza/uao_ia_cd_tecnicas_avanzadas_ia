---
id: TASK-48
title: Memoria conversacional persistente con PostgresChatMessageHistory y ventana temporal
status: To Do
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-11 00:00'
labels:
  - langchain
  - postgres
  - memoria
  - modulo-2
dependencies:
  - TASK-47
references:
  - src/agentes/memoria/historial.py
  - src/api/main.py
documentation:
  - https://python.langchain.com/docs/integrations/memory/
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
priority: high
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El agente debe recordar el hilo conversacional **entre reinicios de contenedores** y **entre peticiones**, asociado a un `session_id` estable por usuario. Se usa **`langchain_postgres.PostgresChatMessageHistory`** (o equivalente soportado en la versión pinneada) sobre PostgreSQL.

## Objetivo

Implementar `src/agentes/memoria/historial.py` con clase **`MemoriaUsuario`** que:

1. Envuelve `PostgresChatMessageHistory(session_id=..., sync_connection=...)` (o patrón recomendado por la versión de `langchain-postgres`).
2. Expone:
   - `cargar_ventana(dias_max: int | None = None, turnos_max: int | None = None) -> list[BaseMessage]` donde `dias_max` por defecto lee **`HISTORIAL_DIAS_MAX`** y `turnos_max` lee **`HISTORIAL_TURNOS_MAX`**, filtrando mensajes con `created_at >= now() - dias_max` (si el backend de LangChain no expone timestamps por mensaje, documentar estrategia alternativa: truncar lista materializada o consulta SQL auxiliar).
   - `agregar_humano(texto: str) -> None`
   - `agregar_ai(texto: str, metadata: dict | None = None) -> None`
3. **`create_tables()`** idempotente invocado desde **lifespan** de FastAPI al inicio (junto con nota en task-46 de que esta tabla no va en Alembic si LangChain la gestiona).

## Tests

Tests con **testcontainers Postgres** o mocks explícitos; si la tabla requiere permisos, documentar en notas.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 `MemoriaUsuario` persiste y recupera mensajes para un `session_id` fijo
- [ ] #2 `create_tables()` es idempotente y se llama desde lifespan sin duplicar esquema
- [ ] #3 Ventana temporal respeta `HISTORIAL_DIAS_MAX` (comportamiento verificable en test con timestamps simulados o datos sembrados)
- [ ] #4 `HISTORIAL_TURNOS_MAX` limita la cantidad de turnos devueltos al router
- [ ] #5 No se registran contenidos sensibles extra en logs
- [ ] #6 Manejo de errores de conexión con mensajes claros en español latinoamericano
- [ ] #7 Tests automatizados o marcador `integration_postgres` con skip documentado
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Revisar documentación de `langchain-postgres` para la versión instalada (API sync vs pool).
2. Implementar fábrica `crear_memoria_usuario(session_id: str, conninfo: str)`.
3. Implementar filtros de ventana (post-proceso o query) según capacidades de la librería.
4. Integrar en lifespan: `create_tables` una vez.
5. Escribir tests con contenedor o mock de historial.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Puede coexistir URL sync (`psycopg`) para LangChain mientras la app usa asyncpg para SQLAlchemy; centralizar `DATABASE_URL_SYNC` en settings.
- Si `PostgresChatMessageHistory` no soporta filtro por fecha nativamente, añadir tabla propia o consulta SQL en `MemoriaUsuario` **sin** romper el formato de mensajes esperado por LangChain.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 `uv run pytest` verde (tests nuevos o skips explícitos)
- [ ] #2 `ruff check` sin errores nuevos
- [ ] #3 Documentar en docstring el contrato de `session_id` alineado a task-47
<!-- DOD:END -->
