---
id: TASK-33
title: >-
  Componente Chat con streaming SSE, render Markdown rico y estado visual de
  carga
status: Done
assignee: []
created_date: '2026-04-30 05:45'
updated_date: '2026-04-30 06:11'
labels:
  - frontend
  - chat
  - streaming
  - markdown
dependencies:
  - TASK-32
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Implementar el flujo de chat principal en `frontend/src/features/chat/`:

- `Chat.tsx`: contenedor principal; gestiona estado local del chat (mensajes, isStreaming, error), llama a streamQa de sseClient.ts
- `MessageList.tsx`: lista scrollable de mensajes; auto-scroll al último mensaje
- `MessageBubble.tsx`: burbuja de mensaje (usuario vs asistente); renderiza Markdown con react-markdown + remark-gfm; syntax highlighting con shiki; modo asistente muestra avatar con logo
- `ChatInput.tsx`: textarea con botón Enviar; Cmd/Ctrl+Enter envía; deshabilita durante streaming; placeholder motivador en español
- Estado «Pensando...»: skeleton loader / indicador de typing mientras llega el primer token
- Manejo de errores: toast con sonner cuando el backend reporta error
- La UI visualmente debe evocar la Vercel AI Chatbot template: burbujas limpias, fondo con sutil gradiente, animación de aparición de mensajes

Dependencias: react-markdown, remark-gfm, shiki (o @shikijs/rehype)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Chat.tsx renderiza MessageList + ChatInput dentro del área principal de AppShell
- [ ] #2 Escribir y enviar una pregunta inicia streaming al backend (POST /api/qa/stream)
- [ ] #3 Tokens aparecen progresivamente en MessageBubble mientras llegan del SSE
- [ ] #4 render Markdown: negritas, listas, enlaces, bloques de código con coloreado sintáctico
- [ ] #5 Skeleton loader visible entre el envío y el primer token
- [ ] #6 Auto-scroll al último mensaje cuando llegan tokens
- [ ] #7 Cmd/Ctrl+Enter en textarea envía el mensaje
- [ ] #8 Toast de error si backend responde con evento error
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Chat.tsx: gestiona estado de turnos (ChatTurn[]), llama a streamQa con handlers onToken/onFuentes/onFinal/onError, diferencia modo single vs dual. MessageList.tsx: auto-scroll con useRef+useEffect, mensaje de bienvenida cuando turns=[]. MessageBubble.tsx: burbujas usuario/asistente con react-markdown+remark-gfm, skeleton cuando isStreaming+content='', cursor parpadeante durante streaming, badge de motor y latencia. ChatInput.tsx: Ctrl+Enter envía, disabled durante streaming.
<!-- SECTION:FINAL_SUMMARY:END -->
