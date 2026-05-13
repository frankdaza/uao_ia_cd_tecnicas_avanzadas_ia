---
id: TASK-49
title: Endpoints API de sesión y dependency obtener_usuario_actual
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-13 00:58'
labels:
  - fastapi
  - api
  - sesion
  - modulo-2
dependencies:
  - TASK-47
  - TASK-48
references:
  - src/api/routers/sesiones.py
  - src/api/esquemas.py
  - src/api/main.py
  - src/api/dependencias.py
  - tests/api/test_sesiones.py
documentation:
  - .claude/skills/fastapi-sse-api/SKILL.md
priority: high
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El frontend necesita **iniciar sesión** con documento de identidad y nombre, recuperar historial para repintar el chat, y que el backend asocie peticiones posteriores al usuario autenticado de forma ligera (sin JWT completo salvo que el equipo lo decida).

## Objetivo

1. Crear router **`src/api/routers/sesiones.py`** con:
   - **`POST /api/sesiones`**: body `{ documento_identidad, nombre }` → upsert vía `RepositorioUsuarios`, actualizar `last_login`, devolver `{ usuario_id, session_id, nombre, ya_existia, ultimo_mensaje_at? }`.
   - **`GET /api/sesiones/actual/historial`**: query `session_id` (o inferido de cookie/header) → lista serializable de mensajes para el frontend (roles, contenido, timestamps si existen).
   - **`POST /api/sesiones/cerrar`**: no-op funcional o limpieza de cookie; registrar intención en logs suave.

2. Definir esquemas Pydantic v2 en **`src/api/esquemas.py`** para request/response anteriores.

3. **Mecanismo de sesión**: elegir y documentar **una** de:
   - Cookie HTTP-only `fvl_session_id` (valor = `session_id`), **o**
   - Header `X-Session-Id` enviado por el cliente.

4. Dependency **`obtener_usuario_actual`** (o nombre equivalente en español ASCII) que resuelve usuario desde cookie/header + validación contra DB.

5. Tests con **`httpx.AsyncClient`** y base de datos de prueba o mocks.

## Seguridad

No almacenar PII innecesaria en logs; no devolver documento completo en respuestas si no hace falta (mascarar en UI es responsabilidad frontend task-58).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `POST /api/sesiones` crea usuario nuevo y devuelve `session_id` canónico
- [x] #2 Usuario existente: `ya_existia=true` y mismo `usuario_id` estable
- [x] #3 `GET .../historial` devuelve mensajes en orden cronológico y formato acordado con frontend
- [x] #4 Mecanismo cookie **o** header documentado en README/doc-003 (task-62)
- [x] #5 Dependency reutilizable por router del agente (task-57)
- [x] #6 Tests API con AsyncClient cubren happy path y 401/403 si sesión inválida
- [x] #7 Esquemas Pydantic con ejemplos `json_schema_extra` opcional para OpenAPI
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Añadir esquemas request/response y enums de rol si aplican.
2. Implementar router con dependencias de sesión DB + repositorio.
3. Integrar lectura de memoria (`MemoriaUsuario`) en endpoint historial.
4. Registrar router en `main.py`.
5. Tests en `tests/api/test_sesiones.py`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- CORS + cookies: si se usa cookie, configurar `CORSMiddleware` con `allow_credentials` y orígenes explícitos.
- Rate limiting: fuera de alcance salvo que el PDF lo exija; mencionar como mejora futura en ADR si aplica.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado router `src/api/routers/sesiones.py` con POST /api/sesiones, GET /api/sesiones/actual/historial y POST /api/sesiones/cerrar. Esquemas Pydantic en `src/api/esquemas.py`. Dependencia `obtener_usuario_actual` en `src/api/dependencias.py` con precedencia X-Session-Id > query session_id > cookie fvl_session_id; reexport de `obtener_sesion_db`. `RepositorioUsuarios.obtener_por_id` para validar UUID de sesion. CORS con allow_credentials=True para cookies. README documenta el mecanismo (sustituye doc-003 aun no creado). Tests en `tests/api/test_sesiones.py` con AsyncClient y overrides/mocks.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest tests/api/test_sesiones.py` verde
- [x] #2 OpenAPI muestra los tres endpoints
- [x] #3 `ruff check` sin errores nuevos
<!-- DOD:END -->
