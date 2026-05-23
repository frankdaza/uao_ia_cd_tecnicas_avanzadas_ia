---
id: TASK-113
title: 'Frontend TAAM: panel seguimiento alertas y conversaciones (UC-MVP-05)'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
updated_date: '2026-05-22 00:47'
labels:
  - modulo-3
  - taam
  - frontend
  - staff
milestone: m-0
dependencies:
  - TASK-108
  - TASK-110
references:
  - proyecto-2/src/api/routers/staff_seguimiento.py
  - proyecto-2/src/api/esquemas_seguimiento.py
  - proyecto-2/frontend/src/features/casos/
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
  - proyecto-2/README.md
modified_files:
  - proyecto-2/frontend/src/lib/schemas.ts
  - proyecto-2/frontend/src/lib/api.ts
  - proyecto-2/frontend/src/lib/useAppPath.ts
  - proyecto-2/frontend/src/App.tsx
  - proyecto-2/frontend/src/features/settings/SettingsPanel.tsx
  - proyecto-2/frontend/src/features/seguimiento/seguimientoPaths.ts
  - proyecto-2/frontend/src/features/seguimiento/severidadStyles.ts
  - proyecto-2/frontend/src/features/seguimiento/SeveridadBadge.tsx
  - proyecto-2/frontend/src/features/seguimiento/ConversacionHilo.tsx
  - proyecto-2/frontend/src/features/seguimiento/AlertaCard.tsx
  - proyecto-2/frontend/src/features/seguimiento/AlertasBandejaPage.tsx
  - proyecto-2/frontend/src/features/seguimiento/CasosSeguimientoListPage.tsx
  - proyecto-2/frontend/src/features/seguimiento/CasoSeguimientoDetallePage.tsx
  - proyecto-2/frontend/src/features/seguimiento/SeguimientoRoutes.tsx
  - proyecto-2/frontend/README.md
  - >-
    backlog/tasks/task-113 -
    Frontend-TAAM-panel-seguimiento-alertas-y-conversaciones-UC-MVP-05.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC-MVP-05** ([casos de uso TAAM](../../docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)): el **personal clínico** (roles `clinico` y `asistente`) revisa el hilo paciente–bot, valida el triage automático y marca alertas como revisadas (doble check). La API staff ya está en **TASK-108** (`GET/PATCH /api/staff/alertas`, `GET .../conversacion`, `GET .../resumen`); login JWT en **TASK-110**.

**Ámbito:** `proyecto-2/frontend/`. Proxy dev: `/api` → `:8001`.

**Dependencias:** TASK-108 (endpoints), TASK-105 (JWT), TASK-112 (casos activos en demo; opcional para navegación cruzada).

## Objetivo

Feature `features/seguimiento/` con rutas SPA bajo `/seguimiento` para bandeja de alertas, listado de casos con indicador de pendientes y detalle de conversación por caso.

## Pantallas (rutas SPA)

| Ruta | Contenido |
|------|------------|
| `/seguimiento` | Bandeja de alertas `revisado=false` (default); tarjetas por severidad; filtros opcionales `severidad`; toggle «Mostrar revisadas» |
| `/seguimiento/casos` | Tabla casos `estado=activo` con badge de alertas pendientes por `caso_id` (conteo desde bandeja) |
| `/seguimiento/caso/{id}` | Metadatos enmascarados, resumen operativo, hilo conversación (burbujas human/assistant), alertas pendientes del caso; **Marcar revisado** |

## Integración API

- `GET /api/staff/alertas?revisado=false&limit=100` — bandeja (orden backend: urgente → seguimiento → info).
- `PATCH /api/staff/alertas/{id}` body `{ "revisado": true }` — invalidar cache react-query de alertas y resumen.
- `GET /api/staff/casos/{id}/conversacion` — mensajes ordenados por `indice`; `404` sin vínculo Telegram.
- `GET /api/staff/casos/{id}/resumen` — última severidad, conteo mensajes, recordatorio.
- `GET /api/staff/casos?estado=activo` — listado con badges (reutilizar cliente TASK-112).

Autenticación: `apiFetch` + Bearer (mismo patrón TASK-110/112).

## UX

- Colores semánticos: `info` (neutro), `seguimiento` (ámbar), `urgente` (rojo/destructive); urgente primero en bandeja (API).
- Polling opcional cada **30 s** en bandeja; toast sonner si aumenta el conteo de pendientes.
- Sin responder por Telegram ni editar mensajes: control deshabilitado + `title` explicativo.
- Errores API en toast español (`detail` del backend).

## Fuera de alcance

- Responder al paciente, intervenir en chat, cerrar caso.
- Tests E2E Playwright.
- Cambios en backend salvo bugfix mínimo.

## Fallas a evitar

- Mostrar PHI completo en demo (confiar en enmascaramiento API para `asistente`).
- Recargar página completa tras PATCH (usar invalidación react-query).
- Omitir estado vacío en bandeja sin vínculo Telegram en detalle.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 La bandeja en `/seguimiento` lista alertas con `revisado=false` desde `GET /api/staff/alertas`; tarjetas muestran severidad (color semántico), paciente, resumen y fecha; urgente visualmente destacado
- [x] #2 #2 Filtro por severidad (`info`/`seguimiento`/`urgente`) y toggle para incluir alertas ya revisadas; al activar revisadas se consulta `revisado=true`
- [x] #3 #3 «Marcar revisado» llama `PATCH /api/staff/alertas/{id}` y la alerta desaparece de la bandeja pendiente sin reload completo (invalidación react-query + toast)
- [x] #4 #4 Detalle `/seguimiento/caso/{id}` muestra conversación ordenada (`indice`), metadatos del caso/resumen y maneja `404` sin vínculo Telegram con mensaje claro
- [x] #5 #5 Listado `/seguimiento/casos` muestra badge con conteo de alertas pendientes por caso (derivado del listado de alertas)
- [x] #6 #6 Polling 30 s en bandeja (opcional desactivable al cambiar de ruta); toast si hay nuevas alertas pendientes respecto al ciclo anterior
- [x] #7 #7 Roles `clinico` y `asistente` acceden a las rutas (mismo JWT staff); sin edición de mensajes (control deshabilitado + texto explicativo)
- [x] #8 #8 `pnpm run build` y `pnpm run lint` en `proyecto-2/frontend/` terminan con código 0
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Esquemas y cliente:** Zod `AlertaTriage`, `ListadoAlertas`, `MensajeConversacion`, `ConversacionCaso`, `CasoResumenSeguimiento`; funciones `listStaffAlertas`, `markAlertaRevisada`, `getStaffConversacion`, `getStaffCasoResumen` en `lib/api.ts`.
2. **Utilidades UI:** `SeveridadBadge`, `seguimientoPaths.ts`, helpers de color severidad.
3. **Páginas:** `AlertasBandejaPage`, `CasosSeguimientoListPage`, `CasoSeguimientoDetallePage`, componente `ConversacionHilo`.
4. **Rutas:** `SeguimientoRoutes.tsx`; registrar en `App.tsx`; enlace «Seguimiento» en `SettingsPanel`.
5. **README frontend:** sección UC-MVP-05, credencial `clinico@demo.taam`, flujo bandeja → detalle → marcar revisado.
6. **Verificación:** `pnpm run build` y `pnpm run lint` en `proyecto-2/frontend/`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **Endpoints:** prefijo `/api/staff/` tag `staff-seguimiento` (ver `proyecto-2/README.md`, `staff_seguimiento.py`).
- **Orden alertas:** urgente → seguimiento → info, luego `created_at` desc (backend).
- **Privacidad:** rol `asistente` recibe `paciente_doc_id` y `telegram_chat_id` enmascarados (últimos 4); `paciente_nombre` sin enmascarar en MVP.
- **Conversación:** checkpointer LangGraph `thread_id` = `telegram:{chat_id}`; roles `human` | `assistant`.
- **Demo:** login `clinico@demo.taam`; caso con Telegram vinculado y alertas sembradas (`sembrar_demo_taam.py` / guion UC sección 11–14).
- **Query keys:** `['staff','alertas', …]`, `['staff','conversacion', casoId]`, `['staff','resumen', casoId]`.
- **Skill:** `react-vite-qa-ui` (react-query + sonner + patrones TASK-112).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Feature `features/seguimiento/` con bandeja `/seguimiento`, listado `/seguimiento/casos` con badges de alertas pendientes y detalle `/seguimiento/caso/{id}` (conversación, resumen, marcar revisado). Cliente API + Zod para endpoints TASK-108; polling 30 s y toast de nuevas alertas; navegación en sidebar y README UC-MVP-05. `pnpm run build` y `pnpm run lint` OK.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Código en `proyecto-2/frontend/src/features/seguimiento/` y rutas en `App.tsx`
- [x] #2 README frontend con flujo UC-MVP-05 y credencial demo clínico
- [x] #3 Sin secretos en el diff; `pnpm run build` y `pnpm run lint` OK
- [x] #4 Tarea marcada Done en Backlog sin `task_complete`
<!-- DOD:END -->
