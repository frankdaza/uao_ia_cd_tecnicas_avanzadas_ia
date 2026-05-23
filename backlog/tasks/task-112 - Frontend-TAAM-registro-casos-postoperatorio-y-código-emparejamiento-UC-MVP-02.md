---
id: TASK-112
title: >-
  Frontend TAAM: registro casos postoperatorio y código emparejamiento
  (UC-MVP-02)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
updated_date: '2026-05-22 00:39'
labels:
  - modulo-3
  - taam
  - frontend
  - asistente
milestone: m-0
dependencies:
  - TASK-102
  - TASK-110
references:
  - proyecto-2/frontend/.env.example
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
  - proyecto-2/src/api/routers/staff_casos.py
  - proyecto-2/src/api/esquemas_casos.py
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
modified_files:
  - proyecto-2/src/api/esquemas_casos.py
  - proyecto-2/src/api/routers/staff_casos.py
  - proyecto-2/tests/api/test_staff_casos.py
  - proyecto-2/README.md
  - proyecto-2/frontend/src/lib/schemas.ts
  - proyecto-2/frontend/src/lib/api.ts
  - proyecto-2/frontend/src/lib/formatApiError.ts
  - proyecto-2/frontend/src/lib/formatFecha.ts
  - proyecto-2/frontend/src/lib/telegramDeepLink.ts
  - proyecto-2/frontend/src/App.tsx
  - proyecto-2/frontend/src/features/settings/SettingsPanel.tsx
  - proyecto-2/frontend/src/features/casos/casosPaths.ts
  - proyecto-2/frontend/src/features/casos/CasosRoutes.tsx
  - proyecto-2/frontend/src/features/casos/CasosListPage.tsx
  - proyecto-2/frontend/src/features/casos/CasoNuevoPage.tsx
  - proyecto-2/frontend/src/features/casos/CodigoEmparejamientoModal.tsx
  - proyecto-2/frontend/src/features/casos/VinculoTelegramBadge.tsx
  - proyecto-2/frontend/README.md
  - proyecto-2/frontend/.env.example
  - proyecto-2/frontend/src/features/shell/PlaceholderCasos.tsx
  - >-
    backlog/tasks/task-112 -
    Frontend-TAAM-registro-casos-postoperatorio-y-código-emparejamiento-UC-MVP-02.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC-MVP-02** ([casos de uso TAAM](../../docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)): el **asistente quirúrgico** registra el caso postoperatorio (sin PDF por paciente) y entrega al paciente un **código de emparejamiento** para vincular Telegram. La API staff ya está en **TASK-102** (`POST/GET /api/staff/casos`, `POST .../codigo-emparejamiento`); el login JWT staff en **TASK-110**.

**Ámbito principal:** `proyecto-2/frontend/`. Proxy dev: `/api` → `:8001`.

**Dependencia mínima de API (si no existe):** `GET /api/staff/tipos-procedimiento?indexacion_estado=ok` para poblar el `<select>` del asistente (el listado admin `/api/admin/procedimientos` exige `rol=admin`). Solo devuelve `id`, `codigo`, `nombre` de tipos indexados.

## Objetivo

Feature `features/casos/` con rutas SPA bajo `/casos` accesibles a cualquier rol staff autenticado (`asistente`, `clinico`, `admin`).

## Pantallas (rutas SPA)

| Ruta | Contenido |
|------|------------|
| `/casos` | Tabla de casos `estado=activo`: paciente, cirujano, fecha cirugía, badge **Vinculado Telegram** (sí/no); acción **Regenerar código** por fila |
| `/casos/nuevo` | Formulario alta: select tipo procedimiento (solo `indexacion_estado=ok`), `paciente_doc_id`, `paciente_nombre`, `cirujano_id`, `cirujano_nombre`, `fecha_cirugia`, `notas_especificas` opcional |

## Flujo tras crear caso

1. `POST /api/staff/casos` → 201 con `id`.
2. Inmediato `POST /api/staff/casos/{id}/codigo-emparejamiento`.
3. **Modal** con código grande, `expira_at` formateado, botón **Copiar código**, texto: «En Telegram envíe `/start CODIGO` al bot».
4. Si `import.meta.env.VITE_TELEGRAM_BOT_USERNAME` está definido, mostrar enlace `https://t.me/{bot}?start={CODIGO}`.

## Integración API

- Autenticación: `apiFetch` + Bearer JWT (mismo patrón TASK-110/111).
- Errores 422 de procedimiento no indexado: mostrar `detail.mensaje` del backend en toast.
- Regenerar código desde listado: mismo modal; invalida el pendiente anterior (comportamiento API TASK-102).

## UX crítica para demo

- Copiar al portapapeles con feedback toast.
- Código legible (tipografía monospace, tamaño grande).
- Listado distingue claramente pendiente vs vinculado.

## Fuera de alcance

- Webhook Telegram, chat clínico, alertas (TASK-106, UC-MVP-03/05).
- Cerrar caso, detalle de conversación.
- Tests E2E Playwright.

## Fallas a evitar

- Select con procedimientos `pendiente`/`error` (el backend rechaza, pero la UI no debe ofrecerlos).
- Omitir TTL/expiración en el modal.
- Usar `listAdminProcedimientos` como única fuente (403 para `asistente@demo.taam`).
- Perder el código tras crear sin modal ni copiar.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 Tras crear un caso válido, la UI muestra modal con código de emparejamiento, fecha/hora de expiración (`expira_at`) e instrucción en español para `/start CODIGO` en Telegram
- [x] #2 #2 El listado en `/casos` muestra badge o columna que distingue `vinculado_telegram` true vs false para casos activos
- [x] #3 #3 El select de tipo de procedimiento solo lista tipos con `indexacion_estado=ok` (vía endpoint staff o filtro equivalente); no aparecen `pendiente`/`error`
- [x] #4 #4 «Regenerar código» llama `POST .../codigo-emparejamiento`, muestra el nuevo código en modal y el listado refleja `codigo_emparejamiento_activo` actualizado tras refetch
- [x] #5 #5 Botón copiar código al portapapeles con toast de confirmación; deep link `t.me/...` visible cuando `VITE_TELEGRAM_BOT_USERNAME` está configurado
- [x] #6 #6 Errores API (401/403/422/5xx) en toast en español usando `detail`/`mensaje` del backend cuando exista
- [x] #7 #7 Layout usable en laptop (~1280px): tabla con scroll horizontal si hace falta; formulario en una columna legible
- [x] #8 #8 `pnpm run build` y `pnpm run lint` en `proyecto-2/frontend/` terminan con código 0
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **API staff tipos (si falta):** `GET /api/staff/tipos-procedimiento?indexacion_estado=ok` en `staff_casos.py` + esquema Pydantic; test mínimo en `test_staff_casos.py`.
2. **Esquemas y cliente:** Zod `Caso`, `CrearCasoBody`, `CodigoEmparejamiento`, `TipoProcedimientoOpcion`; funciones `listStaffTiposProcedimiento`, `createStaffCaso`, `listStaffCasos`, `generateCodigoEmparejamiento` en `lib/api.ts`; extender `formatApiDetail` para `detail` objeto con `mensaje`.
3. **Utilidades:** `telegramDeepLink.ts` (`VITE_TELEGRAM_BOT_USERNAME`); `formatFecha` para cirugía y expiración.
4. **UI:** `CodigoEmparejamientoModal`, `CasosListPage`, `CasoNuevoPage`, `VinculoTelegramBadge`, `CasosRoutes`.
5. **Rutas:** reemplazar `PlaceholderCasos` en `App.tsx`; enlace «Nuevo caso» en `SettingsPanel` si aplica.
6. **README frontend:** sección UC-MVP-02, variable Vite opcional, credencial `asistente@demo.taam`.
7. **Verificación:** `pnpm run build` y `pnpm run lint` en `proyecto-2/frontend/`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **Endpoints staff casos:** prefijo `/api/staff/casos` (ver `proyecto-2/README.md` y `src/api/routers/staff_casos.py`).
- **Tipos para select:** `GET /api/staff/tipos-procedimiento?indexacion_estado=ok` (cualquier rol staff JWT).
- **Demo:** login `asistente@demo.taam`; procedimiento demo `COLE-LAP-001` con `indexacion_estado=ok` (UC sección 10 / `sembrar_demo_taam.py`).
- **Respuesta caso:** incluye `vinculado_telegram`, `codigo_emparejamiento_activo` (pendiente no expirado).
- **Código:** 6–8 caracteres; TTL `TAAM_CODIGO_EMPAREJAMIENTO_TTL_HORAS` (24 h por defecto).
- **Vite:** `VITE_TELEGRAM_BOT_USERNAME` sin `@` → deep link `t.me/{user}?start={codigo}`.
- **Skill:** `react-vite-qa-ui` para patrones react-query + sonner + shadcn.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Feature `features/casos/` con listado `/casos`, alta `/casos/nuevo`, modal de código (copiar, TTL, `/start CODIGO`, deep link opcional). Cliente API staff + Zod; endpoint `GET /api/staff/tipos-procedimiento` para select del asistente. Build y lint OK; test API ampliado.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Código en `proyecto-2/frontend/src/features/casos/` y rutas enlazadas en `App.tsx`
- [x] #2 README frontend actualizado con flujo UC-MVP-02 y variable `VITE_TELEGRAM_BOT_USERNAME` opcional
- [x] #3 Sin secretos ni tokens en el diff; credenciales demo solo referenciadas al `.env.example`
- [x] #4 Tarea marcada Done en Backlog sin invocar `task_complete` (archivo manual)
<!-- DOD:END -->
