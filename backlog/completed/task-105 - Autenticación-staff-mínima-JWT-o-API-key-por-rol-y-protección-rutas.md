---
id: TASK-105
title: Autenticación staff mínima (JWT o API key por rol) y protección rutas
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
updated_date: '2026-05-21 23:52'
labels:
  - modulo-3
  - taam
  - seguridad
  - auth
milestone: m-0
dependencies:
  - TASK-99
modified_files:
  - proyecto-2/pyproject.toml
  - proyecto-2/uv.lock
  - proyecto-2/src/configuracion.py
  - proyecto-2/src/api/auth_staff.py
  - proyecto-2/src/api/esquemas_auth.py
  - proyecto-2/src/api/dependencias.py
  - proyecto-2/src/api/main.py
  - proyecto-2/src/api/routers/auth_staff.py
  - proyecto-2/src/api/routers/staff_casos.py
  - proyecto-2/src/api/routers/admin_procedimientos.py
  - proyecto-2/src/persistencia/modelos.py
  - proyecto-2/src/persistencia/repositorios/usuarios_staff.py
  - proyecto-2/src/persistencia/semilla_staff_demo.py
  - proyecto-2/scripts/sembrar_usuarios_staff_demo.py
  - proyecto-2/tests/api/conftest.py
  - proyecto-2/tests/api/test_auth_staff.py
  - proyecto-2/README.md
  - proyecto-2/.env.example
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Los endpoints staff (`/api/staff/*`) y el panel React (**TASK-109+**) no pueden quedar abiertos. Hoy existe un atajo **`X-Staff-Key` = `STAFF_API_KEY`** (TASK-102) sin roles ni identidad; debe sustituirse por auth ligera sobre la tabla **`usuarios_staff`** (TASK-99).

**Alcance MVP:** JWT de corta vida + dependencia `obtener_staff_actual`; RBAC completo queda fuera. El catálogo admin PDF (`/api/admin/*`) mantiene **`X-Admin-Key`** y además acepta JWT con `rol=admin` (documentar unificación futura con panel).

**No mezclar** cookie/sesión M2 (`proyecto-1`, `X-Session-Id`) con TAAM.

## Objetivo

1. `POST /api/auth/staff/login` con email + contraseña → JWT HS256 (8 h por defecto) con claims `sub` (UUID staff), `rol`, `nombre`, `exp`.
2. Proteger routers staff con `Depends(obtener_staff_actual)` (cabecera `Authorization: Bearer`).
3. Hash **bcrypt** en `usuarios_staff.hash_credencial`; nunca loguear tokens ni contraseñas.
4. Script idempotente de semilla: usuarios demo **asistente**, **clínico** y **admin** (contraseñas solo placeholders en `.env.example`).
5. Tests httpx: login OK/401, ruta staff sin token 401, asistente en ruta solo-admin 403.

## Contrato login

| Campo request | Reglas |
| --- | --- |
| `email` | Email válido, normalizado a minúsculas |
| `password` | `min_length=8` |

| Campo response | Reglas |
| --- | --- |
| `access_token` | JWT firmado con `STAFF_JWT_SECRET` |
| `token_type` | `"bearer"` |
| `expira_en_seg` | Segundos hasta `exp` |
| `rol`, `nombre` | Eco del usuario autenticado |

## Errores HTTP

| Caso | Código | `detail` |
| --- | --- | --- |
| Credenciales incorrectas | 401 | Mensaje genérico (no revelar si falta el email) |
| JWT ausente/inválido/expirado en ruta staff | 401 | Token inválido o ausente |
| Rol insuficiente (p. ej. asistente → `/api/admin/*`) | 403 | Rol no autorizado |
| Auth deshabilitada (`STAFF_JWT_SECRET` vacío) | 503 | Indicar variable de entorno |

## Seguridad y operación

- CORS: `ALLOWED_ORIGINS` ya incluye Vite **5174** (proyecto-2).
- Rate limit en login: **opcional** en MVP; documentar recomendación (proxy/nginx) en README.
- `STAFF_API_KEY` queda **deprecada** para rutas staff; retirar de tests nuevos (compatibilidad no requerida tras esta tarea).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 POST /api/auth/staff/login con credenciales válidas devuelve 200, `access_token` JWT y `token_type=bearer`; credenciales inválidas devuelven 401 con mensaje genérico
- [x] #2 #2 GET o POST bajo `/api/staff/` sin `Authorization: Bearer` devuelve 401
- [x] #3 #3 Usuario con rol `asistente` autenticado recibe 403 al llamar `POST /api/admin/procedimientos`; usuario `admin` con JWT o `X-Admin-Key` recibe 201/200 según el caso
- [x] #4 #4 Usuarios demo (`asistente@demo.taam`, `clinico@demo.taam`, `admin@demo.taam`) y variables `STAFF_JWT_SECRET`, `STAFF_DEMO_*_PASSWORD` documentados en `proyecto-2/README.md` y `.env.example` (placeholders, sin secretos reales en git)
- [x] #5 #5 Tests en `tests/api/test_auth_staff.py` cubren login, ruta staff protegida y RBAC admin; `uv run pytest tests/api/` pasa
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Fase 1 — Configuración y utilidades
1. `uv add pyjwt bcrypt`.
2. En `configuracion.py`: `STAFF_JWT_SECRET`, `STAFF_JWT_EXPIRE_HORAS` (default 8), placeholders `STAFF_DEMO_*_PASSWORD` para el script de semilla.
3. Módulo `src/api/auth_staff.py`: hash/verify bcrypt, emitir y decodificar JWT.

## Fase 2 — Persistencia y semilla
4. `RepositorioUsuariosStaff`: `obtener_por_email`, `crear_o_actualizar_demo`.
5. `scripts/sembrar_usuarios_staff_demo.py` idempotente (asistente, clinico, admin).

## Fase 3 — API
6. `esquemas_auth.py` + router `auth_staff.py`: `POST /api/auth/staff/login`.
7. `dependencias.py`: `obtener_staff_actual`, `requerir_rol_staff`, `requerir_acceso_admin` (JWT admin **o** `X-Admin-Key`).
8. Sustituir `requerir_clave_staff` en `staff_casos.py`; `requerir_clave_admin` → `requerir_acceso_admin` en `admin_procedimientos.py`.
9. Registrar router en `main.py`.

## Fase 4 — Documentación y pruebas
10. Actualizar `.env.example` y `README.md` (usuarios demo, flujo curl con Bearer).
11. `tests/api/test_auth_staff.py` + ajustar `conftest.py` / `test_staff_casos.py`.
12. `uv run pytest tests/api/` verde.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Referencias
- Patrón admin M2: `proyecto-1/src/api/routers/admin.py` (`requerir_clave_admin`, `secrets.compare_digest`).
- Modelo: `src/persistencia/modelos.py` (`UsuarioStaff`, `ROLES_STAFF`).
- Tests API: `tests/api/conftest.py`, `test_staff_casos.py`.
- ADR: `backlog/decisions/decision-7`.

## Claims JWT (HS256)
```json
{"sub": "<uuid>", "rol": "asistente|clinico|admin", "nombre": "...", "exp": ..., "iat": ...}
```

## RBAC mínimo en esta tarea
- `/api/staff/*`: cualquier rol staff autenticado.
- `/api/admin/*`: `rol=admin` en JWT **o** `X-Admin-Key` válida (sin cambiar contrato admin existente).

## Tests sin red
- Fixture que siembra usuarios en SQLite del `app_api` y hace login real.
- Token mock: firmar con el mismo `STAFF_JWT_SECRET` del fixture para probar `obtener_staff_actual` aislado si hace falta.

## TASK-112
El frontend guardará `access_token` en memoria y enviará `Authorization: Bearer`; no usar `localStorage` para la clave admin.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Auth staff JWT: POST /api/auth/staff/login (bcrypt + HS256), obtener_staff_actual en /api/staff/*, requerir_acceso_admin (JWT rol admin o X-Admin-Key), semilla scripts/sembrar_usuarios_staff_demo, tests test_auth_staff.py, README y .env.example actualizados. STAFF_API_KEY deprecado.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 #1 Router `POST /api/auth/staff/login` registrado y visible en OpenAPI tag `auth-staff`
- [x] #2 #2 `scripts/sembrar_usuarios_staff_demo.py` ejecutable tras `alembic upgrade head`
- [x] #3 #3 `uv run pytest tests/api/` verde; sin tokens ni contraseñas en backlog ni logs de prueba
- [x] #4 #4 TASK-112 puede consumir Bearer JWT (nota en implementation notes)
<!-- DOD:END -->
