---
id: TASK-32
title: Cliente HTTP + zod schemas + React Query hooks + transport SSE para streaming
status: Done
assignee: []
created_date: '2026-04-30 05:45'
updated_date: '2026-05-01 01:19'
labels:
  - frontend
  - api-client
  - react-query
  - sse
dependencies:
  - TASK-27
  - TASK-31
priority: high
ordinal: 9
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Implementar la capa de comunicación con el backend en `frontend/src/lib/`:

- `lib/schemas.ts`: tipos y schemas zod para todos los payloads (ModelosRespuesta, QaPeticion, QaRespuesta, FuenteBm25, EventoSse)
- `lib/api.ts`: funciones fetch tipadas para GET /api/modelos, POST /api/qa, POST /api/recargar-corpus; cliente SSE con fetch + ReadableStream + TextDecoderStream (NO EventSource nativo que no soporta POST)
- `hooks/useModels.ts`: hook React Query que llama a GET /api/modelos con cache 30s
- `hooks/useReloadCorpus.ts`: mutation React Query para POST /api/recargar-corpus con toast de éxito/error
- `lib/sseClient.ts`: función streamQa(params, handlers: {onToken, onFuentes, onFinal, onError}) que consume POST /api/qa/stream o /api/qa/dual/stream y despacha eventos

Nota: EventSource nativo solo soporta GET; hay que usar fetch + body JSON + ReadableStream.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 lib/schemas.ts exporta tipos TypeScript y schemas zod para todos los payloads del API
- [ ] #2 lib/api.ts tiene funciones getModelos, postQa, postRecargarCorpus tipadas y con manejo de errores
- [ ] #3 lib/sseClient.ts implementa streaming con fetch + TextDecoderStream (no EventSource)
- [ ] #4 useModels hook retorna {modelos_ollama, modelos_openai, openai_disponible, isLoading, error}
- [ ] #5 useReloadCorpus hook dispara POST y muestra toast via sonner en éxito/error
- [ ] #6 Todos los tipos son inferidos desde zod (z.infer<typeof Schema>)
- [ ] #7 No hay any implícitos: TypeScript strict sin errores
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
lib/schemas.ts: zod schemas + tipos inferidos para ModelosRespuesta, FuenteBm25, QaPeticion, QaRespuesta, EventoSse (discriminatedUnion token/fuentes/final/error), Salud, PromptDefecto, RecargaRespuesta. lib/api.ts: getSalud, getModelos, getPromptDefecto, postRecargarCorpus, postQa con parseJson tipado. lib/sseClient.ts: fetch+ReadableStream+TextDecoderStream (NO EventSource). hooks/useModels.ts, hooks/useReloadCorpus.ts (mutation + toast), hooks/useSalud.ts (polling 15s).
<!-- SECTION:FINAL_SUMMARY:END -->
