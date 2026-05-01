---
id: TASK-26
title: >-
  Endpoints sincrónicos: GET /api/modelos, POST /api/qa, POST
  /api/recargar-corpus
status: Done
assignee: []
created_date: '2026-04-30 05:43'
updated_date: '2026-04-30 05:58'
labels:
  - backend
  - api
  - fastapi
dependencies:
  - TASK-25
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Implementar en `src/api/routers/qa.py` y `src/api/routers/corpus.py` los endpoints sincrónicos:

- `GET /api/modelos`: retorna {modelos_ollama: [...], modelos_openai: [...], openai_disponible: bool}
- `POST /api/qa`: body {pregunta, prompt_sistema, usar_ollama, usar_openai, modelo_ollama, modelo_openai, num_ctx, max_tokens_openai}; retorna {texto_ollama, texto_openai, fuentes, metadatos} según motores activos
- `POST /api/recargar-corpus`: recarga BM25 y retorna {mensaje: '...'}

Reutilizan PipelineQa.responder, responder_openai, responder_dual de src/qa/pipeline.py sin segunda pasada BM25. Errores normalizados a JSON (tipo RFC 7807).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 GET /api/modelos retorna listas de modelos y estado openai_disponible
- [ ] #2 POST /api/qa con solo Ollama activo retorna respuesta Ollama y fuentes BM25
- [ ] #3 POST /api/qa con solo OpenAI activo retorna respuesta OpenAI y fuentes BM25
- [ ] #4 POST /api/qa con ambos activos hace UNA sola pasada BM25 y retorna ambas respuestas
- [ ] #5 POST /api/recargar-corpus llama a recuperador.recargar() y retorna mensaje de éxito
- [ ] #6 Errores (Ollama caído, sin API key) retornan JSON con status y detail, NO traceback
- [ ] #7 Esquemas Pydantic v2 en src/api/esquemas.py para todos los request/response
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementados routers/corpus.py (GET /api/modelos, POST /api/recargar-corpus, GET /api/prompt-defecto) y routers/qa.py (POST /api/qa sincrónico con soporte Ollama/OpenAI/dual). Errores normalizados como HTTPException con status 503/422/402/400 y detail en español. Todos los request/response con modelos Pydantic v2 en esquemas.py.
<!-- SECTION:FINAL_SUMMARY:END -->
