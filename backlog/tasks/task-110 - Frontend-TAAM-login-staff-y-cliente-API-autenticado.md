---
id: TASK-110
title: 'Frontend TAAM: login staff y cliente API autenticado'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
updated_date: '2026-05-22 00:28'
labels:
  - modulo-3
  - taam
  - frontend
  - auth
milestone: m-0
dependencies:
  - TASK-105
  - TASK-109
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
  - proyecto-2/src/api/routers/auth_staff.py
  - proyecto-2/src/api/esquemas_auth.py
modified_files:
  - proyecto-2/frontend/package.json
  - proyecto-2/frontend/pnpm-lock.yaml
  - proyecto-2/frontend/README.md
  - proyecto-2/frontend/src/App.tsx
  - proyecto-2/frontend/src/lib/api.ts
  - proyecto-2/frontend/src/lib/authStorage.ts
  - proyecto-2/frontend/src/lib/schemas.ts
  - proyecto-2/frontend/src/features/auth/AuthContext.tsx
  - proyecto-2/frontend/src/features/auth/StaffLoginScreen.tsx
  - proyecto-2/frontend/src/components/ui/input.tsx
  - proyecto-2/frontend/src/components/ui/label.tsx
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**Módulo 3 (TAAM)** — `proyecto-2/frontend/` tiene shell y stub de auth (TASK-109). El backend expone `POST /api/auth/staff/login` y protege `/api/staff/*` con JWT Bearer (TASK-105). Las pantallas de casos, triage y chat staff **dependen** de esta tarea.

**No mezclar** con sesión M2 (`proyecto-1`: cookie `fvl_session_id`, `X-Session-Id`). TAAM usa solo `Authorization: Bearer <access_token>`.

**Referencias:** `proyecto-2/tests/api/test_auth_staff.py`, semilla demo (`asistente@demo.taam`), `proyecto-1/frontend/src/lib/api.ts` (patrón `ApiError` + handler 401).

## Objetivo

Feature `features/auth/` con login staff real, guard de rutas del SPA y cliente HTTP que adjunta el JWT en todas las peticiones autenticadas futuras.

## Alcance (incluido)

| Área | Entregable |
|------|------------|
| Login | Pantalla `/login`: email + contraseña → `POST /api/auth/staff/login`; validación Zod en cliente |
| Sesión | `AuthProvider`: perfil `nombre` / `rol` / email; token en **sessionStorage** (v1 JSON); **nunca** persistir contraseña |
| API | `lib/api.ts`: `ApiError`, `apiFetch` con `Authorization: Bearer`, `setAuthInvalidHandler` ante 401/403 |
| Rutas | Sin token: cualquier ruta distinta de `/login` redirige a `/login`; con token en `/login` → `/` |
| Logout | Limpia storage, estado React y navega a `/login` (JWT stateless: no hay endpoint revoke en MVP) |
| UX | Toasts `sonner` en español; formulario shadcn (`Input`, `Label`, `Button`) |

## Fuera de alcance

- Refresh token / renovación silenciosa del JWT
- RBAC por rol en UI (solo mostrar `rol` en cabecera)
- Pantallas de negocio (`/casos` real, SSE) — tareas posteriores
- Tests E2E Playwright

## Fallas a evitar

- Token en query string o fragment URL
- `localStorage` para JWT (preferir `sessionStorage` en MVP)
- Rutas del shell accesibles sin guard
- Reutilizar `AuthContext` / cookies de `proyecto-1`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Login con credenciales demo válidas (`POST /api/auth/staff/login`) redirige a `/` y muestra nombre en cabecera
- [x] #2 Sin token, visitar `/` o `/casos` redirige a `/login`; tras login vuelve al shell
- [x] #3 «Cerrar sesión» borra token en sessionStorage y deja la app en `/login` sin datos de perfil
- [x] #4 Una petición autenticada que devuelva 401/403 dispara limpieza de sesión y vuelta a flujo de login (toast opcional)
- [x] #5 Formulario de login usa `Input`, `Label` y `Button` shadcn; errores 401 muestran mensaje en español (toast o inline)
- [x] #6 `pnpm run build` y `pnpm run lint` en `proyecto-2/frontend/` terminan con código 0
- [x] #7 Eliminado el botón «Continuar (desarrollo)» del stub TASK-109
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Dependencias UI:** `sonner`, `@radix-ui/react-label`; componentes `Input` y `Label` bajo `components/ui/`.
2. **Esquemas y API:** `StaffLoginBodySchema` / `StaffLoginResponseSchema` en `schemas.ts`; `api.ts` con `ApiError`, `apiFetch`, `postStaffLogin`, `setAuthInvalidHandler`.
3. **Persistencia:** `authStorage.ts` (clave `taam-staff-auth-v1`, Zod v1: `accessToken`, `email`, `nombre`, `rol`).
4. **AuthProvider:** hidratar desde storage; `signIn` / `signOut`; registrar handler 401 que limpia sesión.
5. **StaffLoginScreen:** formulario email/contraseña, toasts, redirección a `/` en éxito.
6. **App gate:** rutas `/login` vs protegidas con `useAppPath`; quitar `AuthPlaceholder` y `setDevSession`.
7. **Verificación:** `pnpm run build`, `pnpm run lint`; manual con backend 8001 + usuario demo sembrado.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **Endpoint:** `POST /api/auth/staff/login` body `{ email, password }` → `{ access_token, token_type, expira_en_seg, rol, nombre }`.
- **Proxy dev:** igual que TASK-109 — peticiones relativas `/api/*` → `127.0.0.1:8001`.
- **Demo local:** sembrar staff (`scripts/sembrar_usuarios_staff_demo.py` o fixture tests); credenciales en `proyecto-2/.env.example`, no en el frontend.
- **401 global:** `parseJson` invoca `authInvalidHandler` en 401/403; el provider borra storage y `user`.
- **Logout:** no hay `POST /logout` en MVP; basta limpiar cliente (JWT expira en servidor por `exp`).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Login staff JWT en proyecto-2/frontend: StaffLoginScreen en /login, AuthProvider con sessionStorage taam-staff-auth-v1, apiFetch con Bearer y handler 401/403, guard de rutas, sonner, shadcn Input/Label/Button. Stub de desarrollo eliminado. build y lint OK.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Sin imports desde `proyecto-1/frontend`; patrón copiado solo donde aplica (api, shadcn)
- [x] #2 Contraseña no aparece en `sessionStorage`, `localStorage` ni logs
- [x] #3 `AuthPlaceholder` y clave `taam-dev-staff-session` eliminados
- [x] #4 README de `proyecto-2/frontend/` menciona flujo de login y variable `STAFF_JWT_SECRET` en backend (sin secretos)
- [x] #5 Tarea en Backlog con `status: Done`, AC marcados, `finalSummary` actualizado; sin `task_complete`
<!-- DOD:END -->
