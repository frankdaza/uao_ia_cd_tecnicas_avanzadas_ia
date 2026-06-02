---
id: TASK-137
title: 'Frontend TAAM: administración CRUD médicos (panel admin)'
status: Done
assignee:
  - Frank Daza
created_date: '2026-06-02 05:06'
updated_date: '2026-06-02 05:43'
labels:
  - modulo-3
  - taam
  - frontend
  - admin
milestone: m-0
dependencies:
  - TASK-136
references:
  - backlog/tasks/task-136 - Backend-TAAM-catálogo-CRUD-médicos-admin.md
  - >-
    backlog/tasks/task-111 -
    Frontend-TAAM-administración-catálogo-procedimientos-y-PDF-UC-MVP-01.md
  - >-
    backlog/tasks/task-110 -
    Frontend-TAAM-login-staff-y-cliente-API-autenticado.md
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
  - >-
    backlog/tasks/task-111 -
    Frontend-TAAM-administración-catálogo-procedimientos-y-PDF-UC-MVP-01.md
  - proyecto-2/frontend/README.md
modified_files:
  - proyecto-2/frontend/src/features/admin-medicos/AdminMedicosRoutes.tsx
  - proyecto-2/frontend/src/features/admin-medicos/adminMedicosPaths.ts
  - proyecto-2/frontend/src/features/admin-medicos/MedicosListPage.tsx
  - proyecto-2/frontend/src/features/admin-medicos/MedicoNuevoPage.tsx
  - proyecto-2/frontend/src/features/admin-medicos/MedicoDetallePage.tsx
  - proyecto-2/frontend/src/App.tsx
  - proyecto-2/frontend/src/features/settings/SettingsPanel.tsx
  - proyecto-2/frontend/src/lib/api.ts
  - proyecto-2/frontend/src/lib/schemas.ts
  - proyecto-2/frontend/README.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**TASK-136** expone el catálogo REST `/api/admin/medicos` (CRUD JSON, rol admin). El panel TAAM (`proyecto-2/frontend/`) ya tiene el feature espejo **`admin-procedimientos`** (TASK-111): rutas `/admin/procedimientos*`, JWT Bearer vía `apiFetch`, guard RBAC en `App.tsx`, navegación en `SettingsPanel` solo para `user.rol === 'admin'`.

**Usuario demo:** `admin@demo.taam` / contraseña en `.env` (p. ej. `123456789` tras sembrar).

## Objetivo

Feature `features/admin-medicos/` con listado, alta y detalle/edición de médicos, consumiendo la API de TASK-136. Sin `X-Admin-Key` en el navegador.

## Pantallas (rutas SPA)

| Ruta | Contenido |
|------|------------|
| `/admin/medicos` | Tabla: código, nombre, especialidad, activo, fecha alta; enlace detalle; «Nuevo médico» |
| `/admin/medicos/nuevo` | Formulario alta → `POST` JSON |
| `/admin/medicos/{uuid}` | Detalle + `PATCH`; desactivar → `DELETE` (confirmación) |

## Integración API

- `apiFetch` + `Authorization: Bearer` (sessionStorage `taam-staff-auth-v1`).
- Zod en `lib/schemas.ts`; funciones en `lib/api.ts`.
- Errores: `formatApiError` + toast sonner en español.

## Fuera de alcance

- Select de médico en `/casos/nuevo` (tarea futura)
- Tests E2E Playwright
- Gestión usuarios staff
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Listado en /admin/medicos muestra médicos del GET paginado con columnas código, nombre, especialidad y estado activo
- [x] #2 Alta en /admin/medicos/nuevo con POST válido muestra toast de éxito y redirige al listado o detalle
- [x] #3 Detalle permite PATCH de nombre, especialidad y código; errores 409/422 en toast con detail del backend
- [x] #4 Desactivar médico (DELETE) pide confirmación; 409 por casos activos muestra mensaje claro en español
- [x] #5 Rutas /admin/medicos* solo accesibles con user.rol === admin; otros roles redirigen a / con toast
- [x] #6 Validación cliente: codigo_registro ASCII [A-Za-z0-9._-]+; campos requeridos en alta
- [x] #7 pnpm run build y pnpm run lint en proyecto-2/frontend/ terminan con código 0
- [x] #8 frontend/README.md documenta rutas y credencial admin@demo.taam
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Esquemas Zod** en `lib/schemas.ts`: `Medico`, `ListadoMedicosRespuesta`, cuerpos create/patch (alinear con MedicoVista de TASK-136).
2. **Cliente API** en `lib/api.ts`: `listarMedicos`, `obtenerMedico`, `crearMedico`, `actualizarMedico`, `desactivarMedico` usando `apiFetch` + JSON (Content-Type application/json).
3. **Paths** `features/admin-medicos/adminMedicosPaths.ts`: `esRutaAdminMedicos(path)`, helpers parse UUID de detalle.
4. **Páginas:** `MedicosListPage` (react-query useQuery + tabla shadcn); `MedicoNuevoPage` (formulario controlado); `MedicoDetallePage` (useQuery por id + PATCH + botón desactivar con AlertDialog).
5. **Rutas** `AdminMedicosRoutes.tsx`: switch por path como `AdminProcedimientosRoutes`.
6. **App.tsx:** importar rutas; extender guard admin para `esRutaAdminMedicos` (mismo useEffect que procedimientos).
7. **SettingsPanel:** añadir `{ path: '/admin/medicos', label: 'Médicos' }` en NAV_ADMIN.
8. **Validación:** helper `medicosValidacion.ts` o reutilizar regex de procedimientos para código ASCII.
9. **README** `frontend/README.md`: sección CRUD médicos admin.
10. **Verificación:** `pnpm run lint && pnpm run build` en `proyecto-2/frontend/`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Patrón de referencia (DRY)

Copiar estructura de `features/admin-procedimientos/`:
- `AdminProcedimientosRoutes.tsx` → `AdminMedicosRoutes.tsx`
- `ProcedimientosListPage.tsx` → `MedicosListPage.tsx` (sin polling de indexación)
- `ProcedimientoNuevoPage.tsx` → `MedicoNuevoPage.tsx` (JSON, no multipart)

## Ejemplo paths

```typescript
export function esRutaAdminMedicos(path: string): boolean {
  return path === '/admin/medicos' || path.startsWith('/admin/medicos/')
}
```

## Ejemplo API client

```typescript
export async function listarMedicos(params?: { limit?: number; offset?: number; activo?: boolean }) {
  const q = new URLSearchParams()
  if (params?.limit != null) q.set('limit', String(params.limit))
  if (params?.offset != null) q.set('offset', String(params.offset))
  if (params?.activo != null) q.set('activo', String(params.activo))
  const suffix = q.toString() ? `?${q}` : ''
  return apiFetch(`/api/admin/medicos${suffix}`, { schema: listadoMedicosSchema })
}
```

## Guard RBAC en App.tsx

Extender el `useEffect` existente:
```typescript
if (esRutaAdminProcedimientos(path) || esRutaAdminMedicos(path)) {
  // toast + setPath('/') si rol !== admin
}
```

Y en `AppRoutes`:
```typescript
if (esRutaAdminMedicos(path)) {
  return <AdminMedicosRoutes path={path} onNavigate={onNavigate} />
}
```

## Badge activo

Mostrar «Activo» / «Inactivo» con variantes de Badge (mismo estilo que indexacionEstado en procedimientos).

## DELETE UX

`window.confirm` o `AlertDialog` de shadcn: «¿Desactivar este médico?». Si API 409, toast: «No se puede desactivar: tiene casos postoperatorio activos asociados.»

## Dependencias de tarea

**Bloqueante:** TASK-136 desplegado o disponible en dev (`:8001`). No iniciar UI sin contrato API estable.

**Prerequisitos de auth:** TASK-110 (login JWT). **Patrón UI:** TASK-111.

## SOLID en frontend

- **SRP:** una página por flujo (list/create/detail); API en `lib/api.ts`.
- **OCP:** reutilizar `apiFetch`, `formatApiError`, componentes ui/ sin fork.
- **DRY:** no duplicar lógica de guard admin; unificar chequeo de rutas admin.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Feature admin-medicos en proyecto-2/frontend: rutas /admin/medicos* (listado, alta, detalle/PATCH/DELETE), cliente API JSON con JWT, guard RBAC en App.tsx, ítem Médicos en sidebar admin, validación codigo_registro ASCII. pnpm lint y build OK.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 pnpm run build y pnpm run lint en proyecto-2/frontend/ con código 0
- [x] #2 Ítem «Médicos» visible solo en sidebar cuando userRol === admin
- [x] #3 Ninguna petición del navegador usa X-Admin-Key; solo Bearer JWT
- [x] #4 frontend/README.md actualizado con rutas /admin/medicos*
<!-- DOD:END -->
