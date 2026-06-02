---
id: TASK-135
title: >-
  Frontend TAAM: subida de protocolos médicos PDF o Markdown en catálogo admin
  (UC-MVP-01)
status: Done
assignee:
  - Frank Daza
created_date: '2026-06-02 01:47'
updated_date: '2026-06-02 02:14'
labels:
  - modulo-3
  - taam
  - frontend
  - admin
  - markdown
milestone: m-0
dependencies:
  - TASK-134
references:
  - >-
    backlog/tasks/task-111 -
    Frontend-TAAM-administración-catálogo-procedimientos-y-PDF-UC-MVP-01.md
  - >-
    backlog/tasks/task-134 -
    Backend-TAAM-catálogo-acepta-protocolos-médicos-PDF-y-Markdown-UC-MVP-01-dual-format.md
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
  - proyecto-2/frontend/README.md
  - >-
    backlog/tasks/task-111 -
    Frontend-TAAM-administración-catálogo-procedimientos-y-PDF-UC-MVP-01.md
modified_files:
  - proyecto-2/frontend/src/lib/schemas.ts
  - proyecto-2/frontend/src/lib/procedimientosValidacion.ts
  - >-
    proyecto-2/frontend/src/features/admin-procedimientos/ProtocolFileDropZone.tsx
  - >-
    proyecto-2/frontend/src/features/admin-procedimientos/ProcedimientoNuevoPage.tsx
  - >-
    proyecto-2/frontend/src/features/admin-procedimientos/ProcedimientoDetallePage.tsx
  - >-
    proyecto-2/frontend/src/features/admin-procedimientos/ProcedimientosListPage.tsx
  - proyecto-2/frontend/src/features/admin-procedimientos/indexacionEstado.tsx
  - proyecto-2/frontend/README.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Intención del producto

Completar UC-MVP-01 en el panel admin: al subir un **protocolo médico** postoperatorio, el administrador elige **PDF o Markdown** con la misma UX. No se favorece un formato sobre el otro.

## Contexto

- TASK-111 entregó UI **solo PDF** (`PdfDropZone`, validación PDF-only).
- TASK-134 extiende la API con `formato_protocolo` y acepta `.md`.
- Esta tarea es **solo frontend** (`proyecto-2/frontend/`).

## Objetivo

- Alta y reemplazo: drag-and-drop o selector para **PDF o Markdown**.
- Listado y detalle: badge «PDF» / «Markdown» + estado de indexación.
- Mismo polling/reindexación para ambos formatos.
- Mismo `FormData` (`metadata` + `archivo`); sin endpoint nuevo.

## Diseño UI/DRY

| Cambio | Detalle |
|--------|--------|
| PdfDropZone → ProtocolFileDropZone | accept `.pdf,.md` + MIME |
| procedimientosValidacion.ts | `validarArchivoProtocolo()` dual-format |
| schemas.ts | `formato_protocolo: z.enum(['pdf','markdown'])` obligatorio |
| Páginas admin | Copy «Protocolo (PDF o Markdown)» |

## Validación cliente (alineada con TASK-134)

- PDF: extensión .pdf; si `file.type` informado debe ser `application/pdf`.
- Markdown: extensión .md; aceptar `type` vacío, `text/markdown`, `text/plain`, `application/octet-stream`.
- Tamaño ≤ 10 MB (`PROTOCOLO_MAX_BYTES`; alias `PDF_MAX_BYTES` opcional).
- Nombre ASCII `[A-Za-z0-9._-]+`.

## Fuera de alcance

Preview Markdown renderizado, editor in-browser, cambios backend, extensión `.markdown`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 /admin/procedimientos/nuevo: copy y zona de subida indican PDF o Markdown (no solo PDF); accept incluye ambas extensiones y MIME relevantes
- [x] #2 Alta con Markdown exitosa: toast español, badge Markdown, polling de indexación igual que PDF
- [x] #3 Alta con PDF exitosa: regresión completa TASK-111 (mismos toasts, polling, badges)
- [x] #4 Detalle: reemplazo cruzado PDF↔MD; tras refetch muestra formato_protocolo correcto
- [x] #5 Listado: columna o badge de formato por fila
- [x] #6 Drag-and-drop de .md con type vacío o application/octet-stream no rechazado en cliente
- [x] #7 Errores 422 backend visibles en toast con detail en español
- [x] #8 Rutas /admin/procedimientos siguen restringidas a rol=admin
- [x] #9 pnpm run build y pnpm run lint en proyecto-2/frontend/ terminan con código 0
- [x] #10 proyecto-2/frontend/README.md actualizado con PDF y Markdown como formatos equivalentes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Extender `ProcedimientoSchema` en `schemas.ts` con `formato_protocolo` obligatorio.
2. Refactor `procedimientosValidacion.ts`: `validarArchivoProtocolo()`, `PROTOCOLO_MAX_BYTES` (alias `PDF_MAX_BYTES` opcional).
3. Renombrar/generalizar `PdfDropZone` → `ProtocolFileDropZone`; actualizar imports en `ProcedimientoNuevoPage` y `ProcedimientoDetallePage`.
4. Copy UI en español: «Protocolo (PDF o Markdown)» en nuevo, detalle y listado intro.
5. Badge formato en listado/detalle (reutilizar estilo de `indexacionEstado.tsx` o componente `formatoProtocoloBadge.tsx`).
6. Verificar `api.ts`: `createAdminProcedimiento` / `patchAdminProcedimiento` sin Content-Type en FormData.
7. `pnpm run build`, `pnpm run lint`; smoke manual alta PDF y MD con `admin@demo.taam`.
8. Actualizar `proyecto-2/frontend/README.md` sección catálogo admin.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**Proxy dev:** Vite `:5174` → API `:8001`; JWT Bearer vía `apiFetch` (no `X-Admin-Key`).

**Despliegue:** merge/despliegue **después** de TASK-134; `ProcedimientoSchema` exige `formato_protocolo` en JSON.

**Identificadores TS en inglés;** textos UI y toasts en español latinoamericano.

**FormData:** no setear `Content-Type` manual en `api.ts` (boundary multipart).

### Ejemplo validarArchivoProtocolo

```typescript
const MD_MIMES = new Set([
  'text/markdown',
  'text/x-markdown',
  'text/plain',
  'application/octet-stream',
  '',
])

export function validarArchivoProtocolo(
  file: File,
): { ok: true; formato: 'pdf' | 'markdown' } | { ok: false; error: string } {
  const nombre = file.name
  const lower = nombre.toLowerCase()
  if (!NOMBRE_ARCHIVO_ASCII.test(nombre)) {
    return { ok: false, error: 'El nombre solo puede usar letras, números, punto, guion y guion bajo.' }
  }
  if (file.size > PROTOCOLO_MAX_BYTES) {
    return { ok: false, error: `Máximo ${PROTOCOLO_MAX_BYTES / (1024 * 1024)} MB.` }
  }
  if (lower.endsWith('.pdf')) {
    if (file.type && file.type !== 'application/pdf') {
      return { ok: false, error: 'El archivo PDF debe ser application/pdf.' }
    }
    return { ok: true, formato: 'pdf' }
  }
  if (lower.endsWith('.md')) {
    if (file.type && !MD_MIMES.has(file.type)) {
      return { ok: false, error: 'Tipo MIME no reconocido para Markdown (.md).' }
    }
    return { ok: true, formato: 'markdown' }
  }
  return { ok: false, error: 'Use un archivo .pdf o .md.' }
}
```

### Ejemplo ProcedimientoSchema

```typescript
export const ProcedimientoSchema = z.object({
  id: z.uuid(),
  codigo: z.string(),
  nombre: z.string(),
  formato_protocolo: z.enum(['pdf', 'markdown']),
  indexacion_estado: z.enum(['pendiente', 'ok', 'error']),
  qdrant_collection_version: z.number().int().nullable(),
  created_at: z.string(),
})
```

**Demo:** login `admin@demo.taam` tras sembrar backend.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Frontend admin UC-MVP-01: ProtocolFileDropZone acepta PDF y .md con validarArchivoProtocolo; ProcedimientoSchema incluye formato_protocolo; badges PDF/Markdown en listado y detalle; copy y reemplazo cruzado de formatos; README actualizado. pnpm build y lint OK.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Feature admin-procedimientos soporta ambos formatos sin imports desde proyecto-1/frontend
- [x] #2 README frontend documenta PDF y Markdown
- [x] #3 Tarea cerrada con status Done; no usar task_complete automático
<!-- DOD:END -->
