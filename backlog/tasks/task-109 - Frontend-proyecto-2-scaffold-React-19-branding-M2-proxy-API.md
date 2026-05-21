---
id: TASK-109
title: 'Frontend proyecto-2: scaffold React 19, branding M2, proxy API'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
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
priority: high
ordinal: 2130
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Nuevo frontend en `proyecto-2/frontend/` — **implementación nueva**, no copiar árbol de `proyecto-1/frontend/`, pero **misma línea visual** (tokens CSS institucional Lili, Tailwind v4, shadcn/ui).

## Objetivo

Proyecto Vite 8 + TS 6 strict + pnpm 11.x con shell vacío autenticado.

## Entregables

- `package.json` con packageManager pin.
- `vite.config.ts` proxy `/api` → backend proyecto-2 (puerto documentado).
- `styles/globals.css` — reutilizar variables de color/tipografía del diseño M2 (copiar tokens, no componentes de negocio).
- Layout: `AppShell`, tema claro/oscuro (`next-themes`), rutas placeholder.
- ESLint flat config alineado a M2.

## Fallas a evitar

- Importar código TS desde proyecto-1 (prohibido salvo tokens CSS documentados).
- Apuntar proxy al puerto 8000 de M2 por defecto.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 pnpm dev arranca sin errores en proyecto-2/frontend
- [ ] #2 Proxy /api alcanza GET /api/salud del backend TAAM
- [ ] #3 Tema claro/oscuro persiste en localStorage
- [ ] #4 Identificadores TS en inglés; textos UI en español latinoamericano
- [ ] #5 README frontend explica separación respecto a proyecto-1
<!-- AC:END -->
