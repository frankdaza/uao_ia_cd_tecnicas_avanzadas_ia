---
id: TASK-110
title: 'Frontend TAAM: login staff y cliente API autenticado'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
labels:
  - modulo-3
  - taam
  - frontend
  - auth
milestone: m-0
dependencies:
  - TASK-105
  - TASK-109
priority: high
ordinal: 2140
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

TASK-109 creó el shell; TASK-105 expone JWT. Pantallas de negocio dependen de sesión staff.

## Objetivo

Feature `features/auth/`: login, guard de rutas, almacenamiento seguro del token.

## Pantallas

- `/login` — email + contraseña → `POST /api/auth/staff/login`.
- Context `AuthProvider` con refresh de nombre/rol.
- Interceptor `apiClient` adjunta `Authorization: Bearer`.
- Logout limpia token y redirige.

## UX

- Toasts de error en español (credenciales inválidas).
- No guardar contraseña en localStorage.

## Fallas a evitar

- Token en query string.
- Rutas staff accesibles sin guard.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Login exitoso redirige a dashboard placeholder
- [ ] #2 Ruta protegida sin token redirige a /login
- [ ] #3 Logout invalida sesión cliente
- [ ] #4 Manejo 401 global desencadena re-login
- [ ] #5 UI usa componentes shadcn (form, input, button)
<!-- AC:END -->
