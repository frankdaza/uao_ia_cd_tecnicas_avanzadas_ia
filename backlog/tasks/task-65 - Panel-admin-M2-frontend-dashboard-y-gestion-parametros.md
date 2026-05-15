---
id: TASK-65
title: >-
  Panel administrativo M2 (frontend): dashboard, edición de prompts y parámetros
  del modelo, listado de usuarios
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-13 00:00'
updated_date: '2026-05-15 01:01'
labels:
  - modulo-2
  - frontend
  - react
  - admin
  - ux
dependencies:
  - TASK-64
references:
  - frontend/src/App.tsx
  - frontend/src/features/settings/SettingsPanel.tsx
  - frontend/src/lib/api.ts
  - frontend/src/lib/adminFormValidators.ts
  - frontend/src/lib/adminFormValidators.test.ts
  - frontend/src/lib/adminUnauthorized.ts
  - frontend/src/components/ui/table.tsx
  - scripts/README.md
  - frontend/src/lib/adminApi.ts
  - frontend/src/features/admin/AdminEntrada.tsx
  - frontend/src/features/admin/AdminLogin.tsx
  - frontend/src/features/admin/AdminDashboardPage.tsx
  - frontend/src/features/admin/AdminModelPage.tsx
  - frontend/src/features/admin/AdminPromptsPage.tsx
  - frontend/src/features/admin/AdminUsuariosPage.tsx
  - frontend/src/features/admin/AdminLayout.tsx
  - frontend/src/lib/adminSchemas.test.ts
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
priority: high
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Contexto

El chat M2 vive en React 19 + Vite 8 + TypeScript 6 + Tailwind v4 + shadcn/ui ([`frontend/`](frontend/)). El panel lateral actual ([`SettingsPanel.tsx`](frontend/src/features/settings/SettingsPanel.tsx)) es solo informativo. La API administrativa y agregados se implementan en **TASK-64**.

### Objetivo

Construir una **experiencia de panel administrativo** profesional, accesible y coherente con el diseño institucional existente (tokens CSS, tipografía, modo claro/oscuro), que incluya:

1. **Ruta dedicada** (p. ej. `/admin` con React Router o patrón equivalente ya alineado al proyecto) **separada del flujo del usuario final** del chat, evitando que usuarios no autorizados accedan por accidente (entrada explícita por URL + pantalla de acceso con campo para clave admin o flujo acordado con TASK-64).

2. **Dashboard de inicio** dentro del panel:
   - Tarjetas KPI reutilizando componentes shadcn (Card, Badge, Skeleton durante carga).
   - Datos desde los endpoints de agregados de TASK-64 (`@tanstack/react-query`).
   - Layout limpio (grid responsive), jerarquía visual clara y estados vacío/error con mensajes en español latinoamericano.

3. **Sección “Modelo y sampling”** (o nombre equivalente en UI):
   - Formularios controlados para `temperature`, `top_p`, modelos router/compositor, y controles opcionales documentados para `model_kwargs` / `top_k` si el backend los expone.
   - Validación en cliente acorde a límites del API; feedback con toasts (`sonner`) en éxito y error.
   - Botón **Guardar** que dispara `PATCH`/`PUT` admin; tras respuesta OK, invalidar queries para que la vista refleje el estado persistido.

4. **Sección “Prompts”**:
   - Editor de texto multilínea o subformularios para las partes del meta-prompt acordadas en el contrato de TASK-64 (router: `system_prompt`, listas, plantillas; compositor: prompt institucional si aplica).
   - Advertencias UX sobre políticas fijas (p. ej. texto canónico de “sin contexto”) si el backend las exige.
   - Vista previa opcional o diff es “nice to have”; no bloquear entrega si no hay tiempo.

5. **Sección “Usuarios”**:
   - Tabla paginada (Data Table pattern con shadcn) con columnas básicas y formato de fechas localizado.
   - Máscara o truncamiento visual del documento de identidad según lo que devuelva el API.

6. **Calidad frontend**:
   - TypeScript estricto, tipos inferidos o compartidos desde esquemas si el repo introduce OpenAPI client; de lo contrario interfaces TS duplicadas pero alineadas al contrato documentado de TASK-64.
   - Accesibilidad: foco visible, `aria-label` en acciones críticas, contraste suficiente en ambos temas.
   - No almacenar la clave admin en `localStorage` sin cifrado; preferir sesión en memoria + header por petición o cookie `HttpOnly` **solo** si TASK-64 lo implementa — coordinar.

7. **Pruebas**: al menos tests de componente o utilidad para parsers/validadores; opcional Playwright smoke para login admin + guardar parámetro (marcador `e2e` si el repo ya lo usa).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Navegación a `/admin` (o ruta acordada) muestra shell del panel sin romper el flujo del chat en `/` o ruta existente del usuario final
- [x] #2 Dashboard inicial carga KPIs desde API real o mocks en desarrollo con estados loading/error/empty claros
- [x] #3 Formulario de parámetros del modelo permite editar y guardar; tras guardar, una recarga de datos muestra valores persistidos (coherente con TASK-64)
- [x] #4 Sección de prompts permite editar los campos expuestos por el backend y guardar con validación visible
- [x] #5 Tabla de usuarios con paginación funcional y datos básicos
- [x] #6 UI en español latinoamericano; identificadores de código TS/React en inglés según convención del repo
- [x] #7 `pnpm --dir frontend exec eslint` (o comando del proyecto) sin errores nuevos en archivos tocados
- [x] #8 Build de producción `pnpm --dir frontend build` exitoso
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Añadir dependencia de enrutamiento si el bundle actual no tiene router para SPA multi-ruta; configurar `App.tsx` con rutas `/` (chat existente) y `/admin`.
2. Crear layout admin (sidebar interno admin, header con acción cerrar sesión admin si aplica).
3. Implementar hooks `useAdminConfig`, `useAdminUsuarios`, `useAdminMetricas` con react-query y cliente HTTP existente o extendido en [`frontend/src/lib/api.ts`](frontend/src/lib/api.ts).
4. Páginas: `AdminDashboardPage`, `AdminModeloPage`, `AdminPromptsPage`, `AdminUsuariosPage` (nombres PascalCase en inglés).
5. Integración de tema claro/oscuro y tokens ya definidos en [`globals.css`](frontend/src/styles/globals.css).
6. Pruebas y revisión visual manual en viewports móvil y escritorio.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Reutilizar componentes shadcn ya presentes antes de añadir librerías nuevas.
- El proxy Vite hacia `/api` debe cubrir rutas `/api/admin/*`; verificar [`vite.config.ts`](frontend/vite.config.ts).
- **Seguridad UX**: no mostrar la clave admin en pantalla después de enviarla; considerar tiempo de sesión corto en memoria.
- Si el backend devuelve 401, redirigir a pantalla de acceso admin con mensaje genérico (no filtrar si la clave fue incorrecta vs ausente, salvo que el API distinga de forma segura).
- Coordinar con TASK-64 el shape exacto de JSON para evitar drift.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Panel M2 en /admin: login con verificacion GET /api/admin/config (clave solo en memoria), evento global ante 401 + limpieza de cache react-query. Dashboard con KPIs (incluye sesiones_estimadas), estado vacio sin usuarios, queryKeys con adminKey. Modelo/sampling con validacion visible (temperatura 0-2, top_p 0-1, modelos no vacios). Prompts con minimo 80 caracteres visible para prompt institucional. Usuarios con tabla shadcn y paginacion. Nuevos modulos: adminFormValidators (+ tests vitest), adminUnauthorized, table UI; adminApi con verificarClaveAdministracion y emision 401. Documentacion operativa en scripts/README.md (seccion panel frontend). ESLint en archivos admin tocados y pnpm --dir frontend build OK. Chat final en / sin regresiones de rutas (App.tsx).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Flujo manual documentado en comentario de PR o README corto: cómo abrir el panel y qué variable de entorno activa el backend admin
- [x] #2 Sin regresiones en el chat del usuario final (smoke manual o E2E existente)
- [x] #3 Código revisado; sin claves ni tokens hardcodeados
<!-- DOD:END -->
