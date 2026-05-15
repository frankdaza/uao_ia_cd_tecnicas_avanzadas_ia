---
id: TASK-58
title: >-
  Pantalla de identificación (DocId + Nombre), AuthContext y cliente API de
  sesión
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-15 01:01'
labels:
  - frontend
  - auth
  - modulo-2
dependencies:
  - TASK-49
references:
  - frontend/src/features/auth/AuthScreen.tsx
  - frontend/src/features/auth/AuthContext.tsx
  - frontend/src/lib/schemas.ts
  - frontend/src/lib/api.ts
  - frontend/src/App.tsx
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
priority: medium
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El Módulo 2 exige asociar conversaciones a una persona mediante **documento de identidad** y **nombre**, persistiendo memoria en backend. El frontend debe recoger estos datos antes del chat y conservar la sesión entre recargas.

## Objetivo

1. Crear **`frontend/src/features/auth/AuthScreen.tsx`**: formulario con validación **Zod** (documento y nombre requeridos, reglas de formato razonables); submit llama `POST /api/sesiones`.

2. Crear **`frontend/src/features/auth/AuthContext.tsx`**: Provider con estado `{ usuario, sessionId, nombreMostrado?, ... }`, métodos `iniciarSesion`, `cerrarSesion`, y persistencia en **`localStorage`** bajo clave **`fvl-auth-v1`** (solo datos no sensibles: preferir no guardar documento completo si el backend devuelve `session_id` suficiente).

3. Extender **`frontend/src/lib/schemas.ts`**: `SesionPeticionSchema`, `SesionRespuestaSchema`, `HistorialMensajeSchema` (alineados a backend task-49).

4. Extender **`frontend/src/lib/api.ts`**: `iniciarSesion`, `obtenerHistorial` (GET historial con credencial acordada: cookie `credentials: 'include'` o header `X-Session-Id`).

5. Modificar **`frontend/src/App.tsx`**: mostrar `AuthScreen` mientras no exista sesión válida; tras login, renderizar shell de chat.

## Tests

- **Vitest** para AuthContext (serialización localStorage mock).
- **Playwright** e2e: login + reload conserva sesión (según mecanismo elegido).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Usuario sin sesión ve únicamente la pantalla de identificación con textos UI en español latinoamericano
- [x] #2 Validación Zod muestra errores accesibles (ARIA básico)
- [x] #3 Tras login exitoso, `sessionId` disponible para el Chat (task-59)
- [x] #4 Recarga de página restaura sesión desde `localStorage` cuando corresponda
- [x] #5 `cerrarSesion` limpia estado y storage
- [x] #6 Tests Vitest cubren al menos persistencia y error de red
- [x] #7 Playwright: flujo feliz login + reload (skip en CI sin backend si está documentado)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Definir tipos TS (inglés) y schemas Zod compartidos.
2. Implementar `api.ts` con fetch helpers y manejo de errores toast (`sonner`).
3. Implementar `AuthContext` + hook `useAuth`.
4. Implementar `AuthScreen` con componentes shadcn/ui.
5. Integrar en `App.tsx` y rutas/layout existente.
6. Añadir tests.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Alinear con decisión cookie vs header de task-49; si cookie HTTP-only, `localStorage` solo guarda flags mínimos, no el secret.
- No registrar documento de identidad en analytics del navegador.

E2E login+reload: tests/e2e/auth-sesion.spec.ts usa route.fulfill para POST /api/sesiones; en process.env.CI el caso se omite (sin backend). Los tests home usan addInitScript para sembrar fvl-auth-v1.

Cookie HTTP-only fvl_session_id: el cliente también persiste session_id devuelto en JSON para el cuerpo de futuras peticiones (p. ej. agente M2) y cabecera opcional en cierre.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se implementó la pantalla de identificación (DocId + nombre) con validación Zod y textos en español; AuthProvider/useAuth con persistencia en localStorage (clave fvl-auth-v1) guardando usuarioId, sessionId y nombre — sin documento; integración con POST /api/sesiones, GET historial y POST cerrar con credentials e cabecera X-Session-Id opcional. App.tsx muestra AuthScreen sin sesión y AppShell+Chat con sesión; botón Cerrar sesión en cabecera. Tests Vitest (AuthContext + schemas) y Playwright auth-sesion (mock de POST /api/sesiones; omitido en CI según nota en spec).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `pnpm --dir frontend test` verde para tests nuevos/actualizados
- [x] #2 `pnpm --dir frontend exec eslint` sin errores nuevos en archivos tocados
- [x] #3 Contrato JSON verificado contra OpenAPI backend cuando esté disponible
<!-- DOD:END -->
