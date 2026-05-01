---
id: TASK-35
title: DualResponseView con dos columnas y SourcesPanel con cards de fuentes BM25
status: Done
assignee: []
created_date: '2026-04-30 05:45'
updated_date: '2026-05-01 01:19'
labels:
  - frontend
  - chat
  - dual
  - bm25
dependencies:
  - TASK-33
  - TASK-34
priority: high
ordinal: 6
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Implementar el modo de respuesta dual y el panel de fuentes:

- `DualResponseView.tsx`: layout de dos columnas (Ollama | OpenAI) que se activa cuando ambos motores están habilitados; consume POST /api/qa/dual/stream; cada columna tiene su propio MessageBubble con streaming independiente; encabezado de columna con nombre del motor + badge de latencia
- `SourcesPanel.tsx`: panel desplegable debajo del área de chat; muestra cards de las fuentes BM25 recuperadas; cada card: nombre de archivo, score formateado, URL clickable, snippet de 2-3 líneas del contenido
- Aviso de coste dual: Banner/Alert visible cuando ambos motores están activos indicando que se ejecutan dos llamadas LLM
- Transición animada entre modo single y dual
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Cuando ambos motores activos, Chat rende DualResponseView en lugar de MessageBubble simple
- [ ] #2 DualResponseView muestra dos columnas con streaming independiente (eventos SSE con campo motor)
- [ ] #3 SourcesPanel aparece tras recibir evento fuentes con al menos 1 fuente
- [ ] #4 Cards de SourcesPanel muestran nombre, score y URL clickable
- [ ] #5 Aviso de coste dual visible cuando ambos motores activos
- [ ] #6 Modo single y dual comparten el mismo ChatInput sin duplicarlo
- [ ] #7 Transición CSS animada al cambiar entre modos
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
DualResponseView.tsx: grid-cols-1/md:grid-cols-2 para Ollama y OpenAI, banner de aviso de coste dual con AlertTriangle, encabezados de columna con emoji y nombre del motor. SourcesPanel.tsx: cards con nombre/archivo/score/URL clickable, filtrado cuando fuentes=[]. MessageList.tsx diferencia modo dual vs single según turn.modoDual.
<!-- SECTION:FINAL_SUMMARY:END -->
