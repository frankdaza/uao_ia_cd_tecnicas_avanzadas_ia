---
id: TASK-47
title: >-
  Capa de acceso a datos: motor SQLAlchemy async, RepositorioUsuarios y helper
  session_id
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-13 00:58'
labels:
  - sqlalchemy
  - persistencia
  - modulo-2
dependencies:
  - TASK-46
references:
  - src/persistencia/motor.py
  - src/persistencia/repositorios/usuarios.py
  - src/persistencia/repositorios/sesiones.py
  - src/api/main.py
documentation:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
priority: high
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

FastAPI necesita una capa de persistencia async coherente para operaciones sobre `Usuario` y para derivar el identificador de sesión de memoria compatible con LangChain.

## Objetivo

1. **`src/persistencia/motor.py`**: crear `async_engine`, `async_sessionmaker`, y generador/async context `obtener_sesion_db` usable como `Depends` en routers.
2. **`src/persistencia/repositorios/usuarios.py`** — clase `RepositorioUsuarios`:
   - `obtener_por_documento(documento: str) -> Usuario | None`
   - `obtener_o_crear(documento, nombre) -> tuple[Usuario, bool ya_existia]`
   - `actualizar_last_login(usuario_id) -> None`
3. **`src/persistencia/repositorios/sesiones.py`**: helper que devuelve `session_id` canónico `f"user:{usuario_id}"` para vincular con `PostgresChatMessageHistory`.
4. **`src/api/main.py` lifespan**: inicializar engine al arranque y cerrar/dispose al shutdown; registrar en logs errores de conexión sin volcar credenciales.

## Restricciones

- Identificadores Python en español ASCII según reglas del repo.
- No exponer SQL crudo en routers; encapsular en repositorios.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `obtener_sesion_db` funciona como dependencia FastAPI y abre/cierra sesiones correctamente
- [x] #2 `RepositorioUsuarios` cubre upsert lógico o equivalente atómico sin duplicar `documento_identidad`
- [x] #3 `actualizar_last_login` persiste `last_login_at` con timezone UTC o documentado
- [x] #4 Helper `session_id` estable y documentado (formato `user:{uuid}`)
- [x] #5 Lifespan inicializa y cierra el motor sin fugas en reload de uvicorn (notas si hay limitaciones)
- [x] #6 Tests unitarios con SQLite async **no** son obligatorios si el equipo estandariza solo Postgres; preferir tests con contenedor o mocks de sesión
- [x] #7 Logs y mensajes de error en español latinoamericano
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Crear paquete `src/persistencia/` con `__init__.py`.
2. Implementar motor y sessionmaker con settings.
3. Implementar repositorios con inyección de `AsyncSession`.
4. Integrar lifespan en `main.py` y factoría global o `app.state`.
5. Escribir tests mínimos (mock session o testcontainers).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Motor async en ``src/persistencia/motor.py`` con ``expire_on_commit=False``, dependencia ``obtener_sesion_db`` (commit/rollback por peticion).
- ``RepositorioUsuarios`` con ``INSERT ... ON CONFLICT DO NOTHING`` atomico para ``obtener_o_crear``; ``actualizar_last_login`` con UTC.
- ``sesion_id_memoria_langchain`` en ``repositorios/sesiones.py`` (formato ``user:{uuid}``).
- Lifespan en ``src/api/main.py``: crea motor, verifica conexion con log en espanol sin URL, ``dispose`` al apagar. Nota: con ``uvicorn --reload`` cada proceso hijo tiene su propio pool.
- Pruebas: unitaria del helper de session_id; integracion Postgres opcional (``EJECUTAR_INTEGRACION_POSTGRES=1``) para repositorio + Depends.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se implemento la capa de acceso async: motor y factoria de sesiones, dependencia FastAPI con transaccion por peticion, repositorio de usuarios con upsert logico atomico y actualizacion de ultimo acceso en UTC, helper estable ``user:{uuid}`` para LangChain Postgres, y lifespan que inicializa y dispone el motor registrando fallos de verificacion sin exponer credenciales. Pruebas de integracion marcadas ``integration_postgres`` y prueba unitaria del helper de session_id.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest` verde para tests nuevos de persistencia
- [x] #2 `ruff check` sin errores nuevos
- [x] #3 Arranque local con Postgres vacío: app no crashea (migraciones aplicadas vía task-46)
<!-- DOD:END -->
