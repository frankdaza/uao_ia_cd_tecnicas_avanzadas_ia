---
id: TASK-37
title: 'Tests frontend: Vitest + React Testing Library + Playwright E2E'
status: Done
assignee: []
created_date: '2026-04-30 05:46'
updated_date: '2026-04-30 06:11'
labels:
  - frontend
  - tests
  - vitest
  - playwright
dependencies:
  - TASK-36
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Implementar la suite de tests del frontend:

- Vitest + @testing-library/react + @testing-library/user-event para unit/integration
- Tests de: ChatInput (envío, deshabilitar durante stream), MessageBubble (render Markdown), SettingsPanel (toggle visible/oculto), SourcesPanel (render de cards), useModels (mock fetch)
- Playwright para E2E: arrancar el servidor FastAPI de prueba con fixture de mocks LLM; verificar flujo completo de pregunta-respuesta
- `frontend/tests/unit/` y `frontend/tests/e2e/`
- Script pnpm test para Vitest y pnpm test:e2e para Playwright
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 pnpm --dir frontend test pasa sin errores de red real
- [ ] #2 ChatInput.test.tsx: enviar con Enter, deshabilitar durante isStreaming
- [ ] #3 MessageBubble.test.tsx: render de Markdown basico (negrita, lista, codigo)
- [ ] #4 SettingsPanel.test.tsx: toggle Ollama muestra/oculta dropdown de modelo
- [ ] #5 useModels.test.ts: mock de fetch, retorna modelos correctos
- [ ] #6 Playwright: al menos un test E2E contra backend fake que verifica mensaje aparece en pantalla
- [ ] #7 pnpm --dir frontend test:e2e pasa con servidor de prueba local
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Vitest 4.1.5 + @testing-library/react 16.3.2 + @testing-library/user-event + @testing-library/jest-dom + jsdom. vitest.config.ts con alias @/. tests/unit/setup.ts (@testing-library/jest-dom). ChatInput.test.tsx (4 tests: render, enviar, disabled, vacío). MessageBubble.test.tsx (3 tests: user content, Markdown, skeleton). schemas.test.ts (6 tests: validaciones zod). Playwright config + tests/e2e/home.spec.ts (3 tests E2E). 13 unit tests pasan (pnpm test).
<!-- SECTION:FINAL_SUMMARY:END -->
