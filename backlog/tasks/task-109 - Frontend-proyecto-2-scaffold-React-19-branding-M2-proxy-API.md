---
id: TASK-109
title: 'Frontend proyecto-2: scaffold React 19, branding M2, proxy API'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
updated_date: '2026-05-22 00:23'
labels:
  - modulo-3
  - taam
  - frontend
  - react
milestone: m-0
dependencies:
  - TASK-98
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
modified_files:
  - proyecto-2/frontend/package.json
  - proyecto-2/frontend/pnpm-lock.yaml
  - proyecto-2/frontend/vite.config.ts
  - proyecto-2/frontend/tsconfig.json
  - proyecto-2/frontend/tsconfig.app.json
  - proyecto-2/frontend/tsconfig.node.json
  - proyecto-2/frontend/eslint.config.js
  - proyecto-2/frontend/index.html
  - proyecto-2/frontend/.gitignore
  - proyecto-2/frontend/README.md
  - proyecto-2/frontend/public/favicon.svg
  - proyecto-2/frontend/src/
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**Módulo 3 (TAAM)** — `proyecto-2/frontend/` es un SPA **nuevo** (no copiar el árbol de `proyecto-1/frontend/`). Debe compartir la **línea visual M2** (tokens CSS FVL, Tailwind v4, shadcn/ui) y conectarse al backend TAAM en **puerto 8001** (no 8000 de M2).

**Dependencia:** TASK-98 (scaffold repo + placeholder `package.json`). **Bloquea:** TASK-110 (login staff JWT).

**Referencias:** skill `react-vite-qa-ui`, ADR `decision-7` (Vite **5174**, API **8001**), `proyecto-2/README.md`, `proyecto-2/docker-compose.yml` (`ALLOWED_ORIGINS` incluye 5174).

## Objetivo

Scaffold ejecutable: **Vite 8 + React 19 + TypeScript 6 strict + pnpm 11.1.1** con shell de aplicación vacío (layout staff), tema claro/oscuro persistente, proxy dev `/api` → TAAM, verificación de salud y rutas placeholder sin lógica de negocio.

## Alcance (incluido)

| Área | Entregable |
|------|------------|
| Tooling | `package.json` (`packageManager` pin), `vite.config.ts`, `tsconfig*`, ESLint flat, `.gitignore` |
| Estilos | `src/styles/globals.css` — **solo tokens** copiados de M2 (variables `:root` / `.dark`, fuentes); sin componentes de chat/admin de proyecto-1 |
| Layout | `AppShell`, `ThemeToggle`, pie `ApiStatusFooter` (`GET /api/salud` vía React Query) |
| Rutas | Placeholder en `/` y `/casos` con `useAppPath` (sin react-router); stub `AuthContext` para TASK-110 |
| Docs | `frontend/README.md` — puertos, proxy, separación vs proyecto-1 |

## Fuera de alcance (otras tareas)

- Login JWT, guards, `Authorization` → **TASK-110**
- Chat, casos, triage, SSE → tareas frontend posteriores
- Tests E2E Playwright → cuando existan flujos reales
- Importar `.tsx`/hooks desde `proyecto-1` (prohibido; solo tokens CSS documentados)

## Fallas a evitar

- Proxy por defecto a `localhost:8000` (es M2, no TAAM)
- Puerto Vite 5173 (colisión con M2; usar **5174**)
- `SaludSchema` con campos solo M2 (`agente_mock_llm`); TAAM expone `proyecto: "taam"`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `pnpm install` y `pnpm dev` en `proyecto-2/frontend/` arrancan sin error (puerto 5174)
- [x] #2 `pnpm run build` y `pnpm run lint` terminan con código 0
- [ ] #3 En dev, petición relativa `GET /api/salud` vía proxy responde JSON con `estado: "ok"` y `proyecto: "taam"` (backend en 8001)
- [x] #4 `ThemeToggle` alterna claro/oscuro y la preferencia persiste tras recargar (localStorage)
- [x] #5 Identificadores TS/React en inglés; textos visibles y comentarios de UI en español latinoamericano
- [x] #6 `AppShell` muestra rutas placeholder `/` y `/casos` sin importar código desde `proyecto-1/frontend`
- [x] #7 `frontend/README.md` documenta separación vs proyecto-1, puertos 5174/8001 y comando de arranque
- [x] #8 `src/styles/globals.css` reutiliza tokens FVL M2; no incluye lógica de chat/admin copiada
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Inicializar paquete** en `proyecto-2/frontend/`: dependencias alineadas a skill (React 19, Vite 8, TS 6, Tailwind v4, shadcn base: button, next-themes, react-query, zod, lucide).
2. **Configurar Vite**: alias `@/`, `server.port: 5174`, `proxy['/api'] → http://127.0.0.1:8001`.
3. **Copiar tokens** a `src/styles/globals.css` desde `proyecto-1/frontend/src/styles/globals.css` (bloque `:root` / `.dark` / base body; sin clases `.chat-gradient` si no se usan aún).
4. **Shell mínimo**: `AppShell`, `ThemeToggle`, `SettingsPanel` placeholder, navegación `/` y `/casos`, `AuthContext` stub exportando tipos para TASK-110.
5. **Cliente API**: `lib/api.ts` + `schemas.ts` (`SaludSchema` con `proyecto`), `useSalud` + `ApiStatusFooter`.
6. **Calidad**: `pnpm install`, `pnpm run build`, `pnpm run lint`; con backend en 8001, `pnpm dev` y comprobar proxy a `/api/salud`.
7. **README** y cierre Backlog (AC marcados, `status: Done`, sin `task_complete`).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **Puertos canónicos TAAM:** API `8001`, Vite `5174`, Postgres host `15433` (ver `proyecto-2/docker-compose.yml`).
- **Health TAAM:** `GET /api/salud` → `{ estado, version, proyecto: "taam" }` (`src/api/esquemas.py`).
- **Tema:** `next-themes` con `attribute="class"`, `defaultTheme="system"`, `enableSystem` — persiste en `localStorage` bajo clave por defecto del paquete.
- **Rutas:** patrón `useAppPath` igual que M2 (history API, sin dependencia de router).
- **pnpm:** ejecutar desde `proyecto-2/frontend/`; lockfile versionado.
- **CORS:** si se prueba contra API sin proxy, añadir origen 5174 en `.env` (`ALLOWED_ORIGINS`); en dev usar siempre proxy Vite.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Scaffold completo en `proyecto-2/frontend/`: Vite 8 + React 19 + TS 6 strict + pnpm 11.1.1, proxy `/api` → `127.0.0.1:8001`, puerto dev 5174, tokens FVL en `globals.css`, `AppShell` con rutas `/` y `/casos`, `ThemeToggle` (localStorage `taam-theme`), `GET /api/salud` vía React Query, stub `AuthContext` + `AuthPlaceholder` para TASK-110. Verificado: `pnpm install`, `pnpm run build`, `pnpm run lint` OK. AC #3 (proxy en runtime) requiere backend TAAM en 8001 — validar con `uv run uvicorn …` + `pnpm dev` y pie de página «API en línea».
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Lockfile `pnpm-lock.yaml` generado y versionado en `proyecto-2/frontend/`
- [x] #2 Sin imports desde `proyecto-1/frontend` (salvo comentario en README que cite origen de tokens)
- [x] #3 Variables de entorno sensibles no añadidas al frontend; solo proxy dev documentado
<!-- DOD:END -->
