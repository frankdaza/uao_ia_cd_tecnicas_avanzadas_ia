---
id: TASK-139
title: 'Frontend TAAM: combobox de médico en nuevo caso (/casos/nuevo)'
status: Done
assignee:
  - Frank Daza
created_date: '2026-06-02 06:12'
updated_date: '2026-06-02 06:28'
labels:
  - modulo-3
  - taam
  - frontend
  - uc-mvp-02
milestone: m-0
dependencies:
  - TASK-138
references:
  - >-
    backlog/tasks/task-112 -
    Frontend-TAAM-registro-casos-postoperatorio-y-código-emparejamiento-UC-MVP-02.md
  - >-
    backlog/tasks/task-137 -
    Frontend-TAAM-administración-CRUD-médicos-panel-admin.md
  - proyecto-2/frontend/src/features/casos/CasoNuevoPage.tsx
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
  - proyecto-2/frontend/README.md
modified_files:
  - proyecto-2/frontend/src/features/casos/CasoNuevoPage.tsx
  - proyecto-2/frontend/src/features/casos/MedicoCombobox.tsx
  - proyecto-2/frontend/src/features/casos/medicoComboboxUtils.ts
  - proyecto-2/frontend/src/components/ui/popover.tsx
  - proyecto-2/frontend/src/components/ui/command.tsx
  - proyecto-2/frontend/src/lib/api.ts
  - proyecto-2/frontend/src/lib/schemas.ts
  - proyecto-2/frontend/package.json
  - proyecto-2/frontend/pnpm-lock.yaml
  - proyecto-2/frontend/README.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

En `/casos/nuevo` ([`CasoNuevoPage.tsx`](proyecto-2/frontend/src/features/casos/CasoNuevoPage.tsx)) el cirujano se captura con dos `<Input>` manuales (`#cirujano-id`, `#cirujano-nombre`) que el usuario debe tipear (p. ej. `MED-10`). **TASK-136/137** ya administran el catálogo en `/admin/medicos`. **TASK-138** expone `GET /api/staff/medicos` para todo staff JWT.

**Usuario:** admin u otro rol staff en `http://localhost:5174/casos/nuevo` (Vite dev).

## Objetivo

Reemplazar los dos inputs por un **combobox con filtro** que:
- Cargue médicos activos desde `GET /api/staff/medicos` (no `/api/admin/medicos`).
- Muestre cada opción como: `{nombre_completo} — {especialidad || 'Sin especialidad'}`.
- Al seleccionar, envíe en `POST /api/staff/casos`: `cirujano_id` = `codigo_registro`, `cirujano_nombre` = `nombre_completo` (sin cambiar `CrearCasoBodySchema`).

## UX requerida

| Elemento | Comportamiento |
|----------|----------------|
| Label | «Cirujano» (o «Médico / cirujano») |
| Búsqueda | Filtrar por nombre, código o especialidad (case-insensitive) |
| Vacío catálogo | Aviso en español; enlace a `/admin/medicos` solo si `user.rol === 'admin'` |
| Envío | Botón deshabilitado hasta seleccionar médico + resto de campos válidos |
| Errores API | Toast con `formatApiError` (422 validación backend) |

## Fuera de alcance

- Editar médicos desde esta pantalla
- Tests E2E Playwright
- Cambiar contrato API a un solo campo `medico_id` UUID
- FK en base de datos
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 En /casos/nuevo no existen inputs visibles cirujano-id ni cirujano-nombre
- [x] #2 Combobox permite filtrar por nombre, codigo_registro o especialidad (case-insensitive)
- [x] #3 Etiqueta de opción: nombre completo y especialidad; selección obligatoria para habilitar envío
- [x] #4 Tras registrar caso, listados muestran el mismo cirujano_nombre denormalizado
- [x] #5 Si GET /staff/medicos devuelve items vacío, mensaje en español con enlace /admin/medicos solo para rol admin
- [x] #6 Errores 422 del backend se muestran en toast con formatApiError
- [x] #7 pnpm run lint y pnpm run build en proyecto-2/frontend terminan con código 0
- [x] #8 frontend/README.md actualizado en sección UC-MVP-02 / casos
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Esperar TASK-138** desplegado en dev (`GET /api/staff/medicos`).
2. **Zod** en `lib/schemas.ts`: `MedicoOpcionSchema`, `ListadoMedicosOpcionSchema` (alinear campos con backend).
3. **API** en `lib/api.ts`: `listStaffMedicos()` → `GET /staff/medicos` + `parseJson` con schema.
4. **shadcn** (si hace falta): `pnpm dlx shadcn@latest add popover command` en `proyecto-2/frontend/` (repo no tiene Combobox hoy).
5. **Componente** `features/casos/MedicoCombobox.tsx`: props `value`, `onChange`, `items`, `disabled`, `isLoading`; Popover + Command/cmdk o lista filtrada accesible.
6. **CasoNuevoPage**: `useQuery({ queryKey: ['staff','medicos'], queryFn: listStaffMedicos })`; estado `medicoSeleccionado`; eliminar `cirujanoId`/`cirujanoNombre`; integrar combobox; pasar `userRol` desde AuthContext para mensaje vacío.
7. **Validación envío**: `puedeEnviar` exige `medicoSeleccionado != null`; `CrearCasoBodySchema.parse` con ids del catálogo.
8. **README** `frontend/README.md`: documentar combobox y dependencia TASK-138.
9. **Verificación**: `pnpm run lint && pnpm run build`; prueba manual con `admin@demo.taam` en `/casos/nuevo`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Patrón de referencia

- Select de tipo procedimiento en `CasoNuevoPage` (react-query + lista).
- Cliente staff: `listStaffTiposProcedimiento` en `api.ts`.
- Admin médicos (TASK-137): **no** reutilizar `listarMedicos` en casos (RBAC).

## Etiqueta de opción

```typescript
export function etiquetaMedico(m: MedicoOpcion): string {
  const esp = m.especialidad?.trim() || 'Sin especialidad'
  return `${m.nombre_completo} — ${esp}`
}
```

## Filtro cliente

```typescript
function filtrarMedicos(items: MedicoOpcion[], busqueda: string): MedicoOpcion[] {
  const q = busqueda.trim().toLowerCase()
  if (!q) return items
  return items.filter(
    (m) =>
      m.nombre_completo.toLowerCase().includes(q) ||
      m.codigo_registro.toLowerCase().includes(q) ||
      (m.especialidad ?? '').toLowerCase().includes(q),
  )
}
```

## Body al registrar

```typescript
const body = CrearCasoBodySchema.parse({
  paciente_doc_id: pacienteDocId.trim(),
  paciente_nombre: pacienteNombre.trim(),
  tipo_procedimiento_id: tipoId,
  cirujano_id: medicoSeleccionado.codigo_registro,
  cirujano_nombre: medicoSeleccionado.nombre_completo,
  fecha_cirugia: fechaCirugia,
  notas_especificas: notas.trim() || undefined,
})
```

## API client

```typescript
export async function listStaffMedicos(): Promise<ListadoMedicosOpcion> {
  const res = await apiFetch('/staff/medicos')
  return parseJson(res, ListadoMedicosOpcionSchema)
}
```

## Catálogo vacío

```tsx
{medicosQ.isSuccess && medicosQ.data.items.length === 0 ? (
  <p className="rounded-lg border border-amber-500/40 ...">
    No hay médicos activos en el catálogo.
    {user?.rol === 'admin' ? (
      <> <Button variant="link" onClick={() => onNavigate('/admin/medicos')}>Gestionar médicos</Button></>
    ) : (
      ' Solicite a un administrador que registre médicos.'
    )}
  </p>
) : null}
```

## Accesibilidad

- `role="combobox"`, `aria-expanded`, `aria-controls` en trigger.
- Navegación teclado en lista (↑↓, Enter, Escape cierra popover).
- `Label htmlFor` asociado al trigger.

## Prueba manual (checklist)

1. Login `admin@demo.taam`; ir a `/casos/nuevo`.
2. Abrir combobox; buscar «Demo»; seleccionar médico semilla.
3. Completar paciente y tipo; registrar caso; verificar cirujano en `/casos`.
4. (Opcional) Probar filtro por especialidad y código.
5. Con catálogo vacío (BD sin médicos activos), verificar mensaje y enlace admin.

## SOLID / DRY

- **SRP:** `MedicoCombobox` solo UI de selección; página orquesta mutación.
- **DRY:** una función `etiquetaMedico` + `filtrarMedicos`; no duplicar en página.
- **OCP:** combobox reusable si otro flujo staff necesita médico.

## Dependencias

**Bloqueante:** TASK-138 (endpoint staff). **Relacionadas:** TASK-112 (pantalla base), TASK-137 (catálogo admin).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Reemplazados los inputs manuales de cirujano en /casos/nuevo por MedicoCombobox (Popover + cmdk) que consume GET /api/staff/medicos. Schemas MedicoOpcion/ListadoMedicosOpcion, listStaffMedicos en api.ts, mensaje de catálogo vacío con enlace admin condicional, envío con codigo_registro y nombre_completo. pnpm lint y build OK.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Sin console.log ni estado muerto de cirujanoId/cirujanoNombre
- [x] #2 Componente MedicoCombobox aislado; CasoNuevoPage legible
- [x] #3 No se usa listarMedicos de admin en flujo de casos
<!-- DOD:END -->
