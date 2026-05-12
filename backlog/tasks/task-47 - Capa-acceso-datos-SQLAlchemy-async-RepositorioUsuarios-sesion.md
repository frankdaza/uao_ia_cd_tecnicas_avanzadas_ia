---
id: TASK-47
title: 'Capa de acceso a datos: motor SQLAlchemy async, RepositorioUsuarios y helper session_id'
status: To Do
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-11 00:00'
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
ordinal: 5000
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
- [ ] #1 `obtener_sesion_db` funciona como dependencia FastAPI y abre/cierra sesiones correctamente
- [ ] #2 `RepositorioUsuarios` cubre upsert lógico o equivalente atómico sin duplicar `documento_identidad`
- [ ] #3 `actualizar_last_login` persiste `last_login_at` con timezone UTC o documentado
- [ ] #4 Helper `session_id` estable y documentado (formato `user:{uuid}`)
- [ ] #5 Lifespan inicializa y cierra el motor sin fugas en reload de uvicorn (notas si hay limitaciones)
- [ ] #6 Tests unitarios con SQLite async **no** son obligatorios si el equipo estandariza solo Postgres; preferir tests con contenedor o mocks de sesión
- [ ] #7 Logs y mensajes de error en español latinoamericano
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
- Considerar `expire_on_commit=False` para objetos `Usuario` usados tras commit en la misma request.
- UUID: usar tipo nativo Postgres vs `UUID` Python; documentar en ADR si hay elección.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 `uv run pytest` verde para tests nuevos de persistencia
- [ ] #2 `ruff check` sin errores nuevos
- [ ] #3 Arranque local con Postgres vacío: app no crashea (migraciones aplicadas vía task-46)
<!-- DOD:END -->
