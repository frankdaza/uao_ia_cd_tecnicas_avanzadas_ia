---
id: TASK-29
title: >-
  Bootstrap frontend/ con Vite 7 + React 19 + TypeScript strict + ESLint v9 +
  Prettier + pnpm
status: Done
assignee: []
created_date: '2026-04-30 05:44'
updated_date: '2026-04-30 06:10'
labels:
  - frontend
  - vite
  - react
  - typescript
dependencies:
  - TASK-21
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Inicializar el proyecto frontend en `frontend/` usando pnpm y Vite 7 con plantilla React + TypeScript:

- `frontend/package.json`: nombre qa-valledellili-ui, scripts dev/build/preview/test/lint/format
- `frontend/vite.config.ts`: plugin React, alias @/ -> src/, proxy /api -> localhost:8000 en dev
- `frontend/tsconfig.json` + `tsconfig.app.json` + `tsconfig.node.json`: strict mode, paths alias
- `frontend/eslint.config.js`: ESLint v9 flat config con react-hooks, react-refresh, typescript-eslint
- `frontend/prettier.config.cjs`: printWidth 100, singleQuote, tabWidth 2
- `frontend/.editorconfig`
- Actualizar `.gitignore` en raiz: añadir frontend/node_modules, frontend/dist, frontend/.vite

Node 22 LTS. pnpm 10.x. Sin crear aún componentes de UI (eso es task-30+).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 pnpm --dir frontend install sin errores
- [ ] #2 pnpm --dir frontend dev inicia servidor en localhost:5173
- [ ] #3 pnpm --dir frontend build produce dist/ sin errores de TypeScript
- [ ] #4 pnpm --dir frontend lint no reporta errores en el andamiaje inicial
- [ ] #5 Alias @/ funciona (importar desde src/ con @/)
- [ ] #6 Proxy /api en vite.config.ts apunta a http://localhost:8000
- [ ] #7 .gitignore actualizado con entradas de frontend/
- [ ] #8 tsconfig.json usa strict: true
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Bootstrap completo: pnpm create vite frontend --template react-ts. package.json renombrado qa-valledellili-ui con scripts dev/build/preview/test/test:e2e/lint/format. vite.config.ts con @tailwindcss/vite, alias @/, proxy /api->:8000. tsconfig strict:true + ignoreDeprecations:6.0 + paths @/*. prettier.config.cjs + .editorconfig. .gitignore actualizado con frontend/{node_modules,dist,.vite}.
<!-- SECTION:FINAL_SUMMARY:END -->
