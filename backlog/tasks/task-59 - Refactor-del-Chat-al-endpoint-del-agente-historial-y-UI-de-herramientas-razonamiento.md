---
id: TASK-59
title: >-
  Refactor del Chat al endpoint del agente, historial y UI de herramientas /
  razonamiento
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-15 00:07'
labels:
  - frontend
  - chat
  - sse
  - modulo-2
dependencies:
  - TASK-57
  - TASK-58
references:
  - frontend/src/features/chat/Chat.tsx
  - frontend/src/lib/sseClient.ts
  - frontend/src/lib/schemas.ts
  - frontend/src/features/chat/SourcesPanel.tsx
documentation:
  - .claude/skills/react-vite-qa-ui/SKILL.md
priority: medium
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El chat actual consume `/api/qa/stream` y modelos legacy. Debe migrar a **`/api/agente/stream`**, mostrar historial recuperado del backend, y dar **transparencia** sobre qué tool usó el router (FAQ vs RAG denso) y las fuentes vectoriales.

## Objetivo

1. Al montar `Chat`, llamar **`obtenerHistorial(sessionId)`** y rellenar estado de mensajes (`turns`).

2. Si el historial no está vacío o es primer ingreso con `primer_turno`, disparar flujo acordado para saludo (evento token inicial o petición explícita con `primer_turno=true`).

3. Reemplazar `streamQa('/api/qa/stream', ...)` por **`streamAgente('/api/agente/stream', ...)`** en **`frontend/src/lib/sseClient.ts`** con handlers:
   - `onPensamiento`, `onHerramienta`, `onToken`, `onFuentes`, `onFinal`, `onError` (nombres en inglés en código).

4. **UI**:
   - Badge por mensaje del asistente: **"Tool: FAQ"** vs **"Tool: RAG denso"**.
   - Panel colapsable **"Razonamiento del router"** con eventos de pensamiento.
   - `SourcesPanel` extendido para listar fuentes Qdrant (`archivo`, `titulo`, `source_url`, `score`).

5. Limpiar **`frontend/src/lib/schemas.ts`** de tipos exclusivos de `qa/stream` y modo dual obsoleto; mantener componentes `MessageList`, `MessageBubble` con extensiones mínimas.

## Tests

Actualizar **Vitest** (`Chat.test.tsx`, `sseClient.test.ts`, `schemas.test.ts`) al nuevo contrato SSE.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Ninguna llamada residual a `/api/qa/stream` en código productivo del frontend
- [x] #2 Historial inicial visible tras login sin duplicar mensajes del usuario
- [x] #3 SSE parsea todos los tipos de evento definidos en task-57
- [x] #4 UI muestra badge de tool y panel de razonamiento colapsable
- [x] #5 Fuentes RAG renderizan enlaces clickeables cuando hay `source_url`
- [x] #6 Estados de carga / error con mensajes en español latinoamericano
- [x] #7 `pnpm --dir frontend test` verde
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Actualizar Zod schemas de eventos SSE agente.
2. Implementar parser incremental en `sseClient.ts`.
3. Refactor `Chat.tsx` state machine (idle/streaming/error).
4. Ajustar componentes de mensaje para metadata de tool.
5. Extender `SourcesPanel` props.
6. Tests RTL + mocks de fetch/stream.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Mantener accesibilidad: panel colapsable con `button` + `aria-expanded`.
- Evitar fugas de PII en panel de razonamiento (mostrar solo resúmenes seguros).

ESLint react-hooks/set-state-in-effect: carga de historial mueve setState al inicio del async IIFE; sin sessionId se limpia con queueMicrotask.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
El chat usa `streamAgente` hacia `/api/agente/stream` con cuerpo `AgentePeticion` (session_id, pregunta, primer_turno). Al montar se llama `getHistorialSesion(sessionId)` y se mapean pares human/ai a turnos sin duplicar envíos del usuario. Zod: `EventoAgenteSseSchema` (pensamiento, herramienta, token, fuentes con chunks RAG, final, error). UI: badge de tool (FAQ vs RAG denso), panel colapsable "Razonamiento del router", `SourcesPanel` con chunks y enlaces `source_url`. Estados de carga/error en español; Vitest y ESLint en archivos tocados verdes.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `pnpm --dir frontend test` verde
- [x] #2 Smoke manual contra backend con agente real o mock
- [x] #3 ESLint sin errores nuevos en archivos tocados
<!-- DOD:END -->
