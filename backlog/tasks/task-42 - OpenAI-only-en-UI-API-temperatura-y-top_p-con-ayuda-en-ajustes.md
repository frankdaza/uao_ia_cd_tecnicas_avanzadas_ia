---
id: TASK-42
title: OpenAI-only en UI/API; temperatura y top_p con ayuda en ajustes
status: Done
assignee: []
created_date: '2026-05-12 03:53'
updated_date: '2026-05-15 01:01'
labels:
  - frontend
  - api
  - qa
  - settings
  - openai
dependencies: []
references:
  - src/api/esquemas.py
  - src/api/routers/qa.py
  - src/qa/pipeline.py
  - src/qa/cliente_openai.py
  - frontend/src/features/settings/SettingsPanel.tsx
  - frontend/src/features/chat/Chat.tsx
modified_files:
  - src/api/esquemas.py
  - src/api/routers/qa.py
  - src/api/main.py
  - src/qa/cliente_openai.py
  - src/qa/pipeline.py
  - frontend/src/features/settings/SettingsContext.tsx
  - frontend/src/features/settings/SettingsPanel.tsx
  - frontend/src/features/chat/Chat.tsx
  - frontend/src/lib/schemas.ts
  - frontend/src/lib/sseClient.ts
  - tests/api/conftest.py
  - tests/api/test_qa.py
  - tests/api/test_stream.py
  - tests/api/test_modelos.py
  - tests/api/test_concurrent_openai_sampling.py
  - tests/qa/test_pipeline.py
  - tests/qa/test_prompt.py
  - frontend/tests/unit/schemas.test.ts
  - frontend/tests/unit/sseClient.test.ts
  - frontend/tests/unit/Chat.test.tsx
  - frontend/tests/unit/SettingsPersistence.test.tsx
priority: high
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Producto solo OpenAI: quitar switch Usar Ollama, selector modelo Ollama y num_ctx del panel y del contrato PeticionQa; simplificar routers QA (sin dual stream en producto). Anadir temperatura y top_p a PeticionQa con validacion Pydantic, propagar a ClienteOpenAi (REST + SSE). UI: sliders + Tooltip en espanol latinoamericano. Codigo interno ClienteOllama puede permanecer para scripts pero no se expone en HTTP. Cambio rompente del JSON de POST /api/qa y SSE.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 PeticionQa solo campos OpenAI + temperatura + top_p; sin usar_ollama/modelo_ollama/num_ctx
- [x] #2 POST /api/qa y POST /api/qa/stream solo OpenAI; dual stream eliminado o no registrado
- [x] #3 ClienteOpenAi pasa temperature y top_p a chat.completions
- [x] #4 SettingsPanel sin bloque Ollama; temperatura y top_p con ayuda contextual
- [x] #5 Tests api y frontend actualizados
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
PeticionQa reducida a OpenAI con temperatura y top_p (Pydantic). qa.py: solo POST /api/qa y /api/qa/stream; eliminado dual/stream. ClienteOpenAi y pipeline propagan temperatura/top_p. Frontend: fvl-settings-v2, SettingsPanel sin Ollama, sliders con tooltips ES, Chat solo openai/stream. Tests api/qa ajustados; test_concurrent_num_ctx reemplazado por test_concurrent_openai_sampling. Alineacion de tests prompt/pipeline/modelos con estado actual del repo.
<!-- SECTION:FINAL_SUMMARY:END -->
