---
id: TASK-111
title: 'Frontend TAAM: administración catálogo procedimientos y PDF (UC-MVP-01)'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
updated_date: '2026-05-22 00:34'
labels:
  - modulo-3
  - taam
  - frontend
  - admin
milestone: m-0
dependencies:
  - TASK-100
  - TASK-110
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
  - proyecto-2/src/api/routers/admin_procedimientos.py
  - proyecto-2/README.md
modified_files:
  - proyecto-2/frontend/src/lib/api.ts
  - proyecto-2/frontend/src/lib/schemas.ts
  - proyecto-2/frontend/src/lib/formatApiError.ts
  - proyecto-2/frontend/src/lib/formatFecha.ts
  - proyecto-2/frontend/src/lib/procedimientosValidacion.ts
  - proyecto-2/frontend/src/App.tsx
  - proyecto-2/frontend/src/features/settings/SettingsPanel.tsx
  - >-
    proyecto-2/frontend/src/features/admin-procedimientos/AdminProcedimientosRoutes.tsx
  - >-
    proyecto-2/frontend/src/features/admin-procedimientos/adminProcedimientosPaths.ts
  - proyecto-2/frontend/src/features/admin-procedimientos/indexacionEstado.tsx
  - proyecto-2/frontend/src/features/admin-procedimientos/PdfDropZone.tsx
  - >-
    proyecto-2/frontend/src/features/admin-procedimientos/ProcedimientosListPage.tsx
  - >-
    proyecto-2/frontend/src/features/admin-procedimientos/ProcedimientoNuevoPage.tsx
  - >-
    proyecto-2/frontend/src/features/admin-procedimientos/ProcedimientoDetallePage.tsx
  - proyecto-2/frontend/README.md
  - >-
    backlog/tasks/task-111 -
    Frontend-TAAM-administración-catálogo-procedimientos-y-PDF-UC-MVP-01.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC-MVP-01** ([casos de uso TAAM](../../docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)): el administrador de catálogo registra tipos de procedimiento con PDF de protocolo. El backend ya expone `POST/GET/PATCH /api/admin/procedimientos` y `POST .../reindexar` (**TASK-100**, ingesta en background **TASK-101**). El login staff JWT (**TASK-110**) permite acceso admin con `rol=admin` (`admin@demo.taam`).

**Ámbito:** `proyecto-2/frontend/` únicamente. Proxy dev: `/api` → `:8001`.

## Objetivo

Feature `features/admin-procedimientos/` para listar, crear y mantener el catálogo, mostrando **estado de indexación** (`pendiente` / `ok` / `error`) y versión vectorial Qdrant.

## Pantallas (rutas SPA)

| Ruta | Contenido |
|------|------------|
| `/admin/procedimientos` | Tabla: código, nombre, versión vector, estado indexación, fecha alta; enlace a detalle y botón «Nuevo procedimiento» |
| `/admin/procedimientos/nuevo` | Formulario: código (ASCII), nombre, PDF (drag-drop o selector); validación tamaño ≤10 MB y nombre archivo ASCII en cliente |
| `/admin/procedimientos/{id}` | Detalle + PATCH metadata; reemplazar PDF; botón «Reindexar» → `POST .../reindexar` |

## Integración API

- Autenticación: **`apiFetch`** con `Authorization: Bearer` (JWT staff `rol=admin`). No usar `X-Admin-Key` en el panel web.
- Alta/actualización: `multipart/form-data` — campo `metadata` (JSON string) + `archivo` (PDF).
- Polling opcional (react-query `refetchInterval`) mientras haya filas con `indexacion_estado=pendiente`.

## Fuera de alcance

- Gestión de usuarios staff, casos, chat o alertas
- Ingesta manual por script (solo botón reindexar vía API)
- Tests E2E Playwright

## Fallas a evitar

- Subir PDF sin feedback de indexación (usuario no sabe si el RAG está listo)
- Omitir validación de tamaño/tipo en cliente antes del upload
- Permitir rutas `/admin/*` a usuarios con rol `asistente` o `clinico`
- Forzar `Content-Type: application/json` en `FormData` (rompe el boundary multipart)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 Alta con PDF (`POST` multipart) muestra toast de éxito y el procedimiento aparece en el listado con `indexacion_estado` visible
- [x] #2 #2 Listado y detalle muestran estado de indexación con etiquetas en español (`pendiente`, `listo`, `error`) y versión vector cuando aplique
- [x] #3 #3 Errores de API (401/403/409/422/5xx) se muestran en toast en español usando el `detail` del backend cuando exista
- [x] #4 #4 Rutas bajo `/admin/procedimientos` solo accesibles con `user.rol === 'admin'`; otros roles redirigen a `/` con mensaje
- [x] #5 #5 Validación en cliente: PDF ≤10 MB, nombre de archivo ASCII `[A-Za-z0-9._-]+`, código ASCII; formulario deshabilitado si falla
- [x] #6 #6 Tras crear o reemplazar PDF, la UI indica indexación en curso (spinner o badge `pendiente`) y refresca el estado (polling o refetch manual)
- [x] #7 #7 Layout usable en viewport laptop (~1280px): tabla con scroll horizontal si hace falta; formulario en una columna legible
- [x] #8 #8 `pnpm run build` y `pnpm run lint` en `proyecto-2/frontend/` terminan con código 0
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Esquemas y API:** Zod para `Procedimiento`, listado paginado; funciones `list/get/create/patch/reindex` en `lib/api.ts`; `apiFetch` sin Content-Type en `FormData`; helper `formatApiError` para `detail` string o array (422).
2. **Utilidades:** constantes PDF (10 MB, regex nombre ASCII); mapa de etiquetas/colores para `indexacion_estado`.
3. **UI:** `PdfDropZone`, páginas listado/alta/detalle con react-query + sonner.
4. **Rutas y RBAC:** en `App.tsx` enrutar `/admin/procedimientos*`; guard: si `user.rol !== 'admin'` → toast + redirección `/`; ítem de navegación solo visible para admin en `SettingsPanel`.
5. **README frontend:** sección catálogo admin y credencial `admin@demo.taam`.
6. **Verificación:** `pnpm run build` y `pnpm run lint` en `proyecto-2/frontend/`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **Endpoints:** prefijo `/api/admin/procedimientos` (ver `proyecto-2/README.md`).
- **Demo:** login `admin@demo.taam` + contraseña en `proyecto-2/.env.example`; `asistente@demo.taam` debe recibir 403 si intenta la API (ya cubierto en tests).
- **Respuesta recurso:** `id`, `codigo`, `nombre`, `indexacion_estado`, `qdrant_collection_version`, `created_at`.
- **Reindexar:** 202 Accepted; deja `indexacion_estado=pendiente` y encola ingesta.
- **Errores:** 409 código duplicado; 422 PDF/metadata; mostrar `detail` en toast español.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Panel admin UC-MVP-01 en proyecto-2/frontend: feature admin-procedimientos con listado, alta multipart, detalle (metadata, reemplazo PDF, reindexar), badges de indexación, polling 3s en pendiente, guard rol admin, API en lib/api.ts con FormData y Zod. build y lint OK.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 #1 Feature en `proyecto-2/frontend/src/features/admin-procedimientos/` sin imports desde `proyecto-1/frontend`
- [x] #2 #2 `lib/api.ts` y `schemas.ts` documentan contrato UC-MVP-01; multipart sin romper Bearer
- [x] #3 #3 README de `proyecto-2/frontend/` describe rutas admin, rol requerido y flujo de subida PDF
- [x] #4 #4 Tarea en Backlog con `status: Done`, AC marcados y `finalSummary`; sin `task_complete`
<!-- DOD:END -->
