---
id: TASK-27
title: >-
  Endpoints SSE: POST /api/qa/stream y POST /api/qa/dual/stream con
  sse-starlette
status: Done
assignee: []
created_date: '2026-04-30 05:44'
updated_date: '2026-05-01 01:21'
labels:
  - backend
  - api
  - sse
  - streaming
dependencies:
  - TASK-26
priority: high
ordinal: 14
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Implementar los endpoints de streaming token a token usando sse-starlette:

- `POST /api/qa/stream`: SSE para Ollama individual o OpenAI individual
- `POST /api/qa/dual/stream`: SSE secuencial Ollama -> OpenAI con UNA sola pasada BM25

Eventos SSE: `token` (texto parcial), `fuentes` (BM25 sources JSON), `final` (metadatos completos), `error` (mensaje de error), `keepalive` (heartbeat cada 15s).

Reutiliza los generadores existentes en src/qa/pipeline.py: responder_stream, responder_openai_stream, stream_ollama_desde_contexto, stream_openai_desde_contexto.

Cada evento SSE lleva campo `motor` (ollama|openai) para que el frontend diferencie en modo dual.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 POST /api/qa/stream emite eventos SSE token a token desde Ollama
- [ ] #2 POST /api/qa/stream emite eventos SSE token a token desde OpenAI
- [ ] #3 POST /api/qa/dual/stream emite primero tokens Ollama (motor=ollama) luego tokens OpenAI (motor=openai)
- [ ] #4 UNA sola pasada BM25 en modo dual (preparar_contexto_inferencia llamado una vez)
- [ ] #5 Evento fuentes emitido tras completar cada respuesta con array de FuenteBm25 serializado
- [ ] #6 Evento error emitido (no excepción no controlada) si Ollama caído o sin API key
- [ ] #7 Heartbeat keepalive cada 15 segundos para conexiones largas
- [ ] #8 Content-Type: text/event-stream con charset=utf-8
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementados en routers/qa.py: POST /api/qa/stream (Ollama o OpenAI individual) y POST /api/qa/dual/stream (Ollama→OpenAI secuencial, una sola pasada BM25 via preparar_contexto_inferencia). Generadores async_gen que envuelven generadores sync con asyncio.to_thread. Eventos SSE: token, final, fuentes, error. Heartbeat keepalive=15s configurado en EventSourceResponse. Campo motor en cada evento para que el frontend diferencie columnas.
<!-- SECTION:FINAL_SUMMARY:END -->
