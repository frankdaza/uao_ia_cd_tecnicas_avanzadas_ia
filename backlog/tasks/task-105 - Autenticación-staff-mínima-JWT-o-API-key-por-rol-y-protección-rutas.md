---
id: TASK-105
title: Autenticación staff mínima (JWT o API key por rol) y protección rutas
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
labels:
  - modulo-3
  - taam
  - seguridad
  - auth
milestone: m-0
dependencies:
  - TASK-99
priority: high
ordinal: 2090
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Endpoints staff (`/api/staff/*`) y panel React no pueden quedar abiertos. RBAC completo está fuera de MVP, pero se requiere barrera mínima antes de frontends (TASK-109+).

## Objetivo

Auth ligera para asistentes y personal clínico usando tabla `usuarios_staff` (TASK-99).

## Opción recomendada MVP

- `POST /api/auth/staff/login` → token JWT corta vida (8h) con claims: `sub`, `rol`, `nombre`.
- Dependencia FastAPI `obtener_staff_actual` en routers staff.
- Semilla: 2 usuarios demo en script (asistente + clinico) con contraseñas en `.env.example` como placeholders.
- Admin catálogo PDF puede seguir `X-Admin-Key` **o** rol admin en JWT (documentar unificación).

## Seguridad

- Hash bcrypt/argon2 para contraseñas; nunca loguear tokens.
- CORS acotado a origen del frontend proyecto-2.
- Rate limit básico en login (opcional pero documentado).

## Fallas a evitar

- Mezclar cookie de sesión M2 (proyecto-1) con TAAM.
- Tokens sin expiración.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Login válido devuelve JWT; inválido 401
- [ ] #2 Ruta staff protegida rechaza petición sin token (401)
- [ ] #3 Rol asistente no puede llamar endpoints solo-admin si se separan
- [ ] #4 Usuarios demo documentados en README y .env.example
- [ ] #5 Tests de dependencia con token mock
<!-- AC:END -->
