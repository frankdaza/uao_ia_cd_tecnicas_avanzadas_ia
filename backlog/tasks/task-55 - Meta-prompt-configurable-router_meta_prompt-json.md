---
id: TASK-55
title: Meta-prompt configurable en config/router_meta_prompt.json y cargador con caché
status: To Do
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-11 00:00'
labels:
  - router
  - configuracion
  - modulo-2
dependencies:
  - TASK-50
  - TASK-51
references:
  - config/router_meta_prompt.json
  - src/agentes/meta_prompt.py
  - tests/agentes/test_meta_prompt.py
documentation:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
priority: high
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El comportamiento del router debe ajustarse **sin redeploy de código** para iteraciones pedagógicas: reglas de cuándo usar FAQ vs RAG, ejemplos few-shot y plantillas de saludo.

## Objetivo

1. Crear **`config/router_meta_prompt.json`** con estructura mínima:
   ```json
   {
     "version": 1,
     "modelo_router": "gpt-4o-mini",
     "system_prompt": "...",
     "herramientas": [
       { "name": "faq_estructurada", "description": "...", "when_to_use": "...", "ejemplos": [] },
       { "name": "rag_denso", "description": "...", "when_to_use": "...", "ejemplos": [] }
     ],
     "reglas_decision": ["..."],
     "respuesta_sin_contexto": "No tengo información suficiente",
     "saludo_template": "Hola {nombre}, ..."
   }
   ```
   El `system_prompt` debe instruir al LLM del router a **emitir tool-calls** (no texto libre) según las reglas.

2. Implementar **`src/agentes/meta_prompt.py`**:
   - Carga JSON con **caché por mtime** (recargar si el archivo cambia en disco).
   - Validación con **modelo Pydantic** dedicado (`MetaPromptConfig` o similar) y tests de schema.

3. Tests que cubren JSON inválido, versión inesperada y hot-reload simulado (tocar tmp file en test).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 Archivo JSON versionado bajo `config/` y montado ro en Docker (task-45)
- [ ] #2 Validación Pydantic rechaza configuraciones incompletas con errores legibles
- [ ] #3 Caché por `mtime` verificable en test (dos cargas, segunda tras `touch`)
- [ ] #4 `reglas_decision` y `herramientas` cubren ambas tools (`faq_estructurada`, `rag_denso`)
- [ ] #5 `saludo_template` documenta placeholders soportados (`{nombre}` mínimo)
- [ ] #6 `respuesta_sin_contexto` alineado con política Lili / `src/qa/prompt.py`
- [ ] #7 Tests `tests/agentes/test_meta_prompt.py` pasan
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Definir schema Pydantic v2 reflejando el JSON.
2. Implementar loader con `pathlib.Path.stat().st_mtime`.
3. Redactar contenido inicial del JSON en español latinoamericano (instrucciones al modelo).
4. Tests de validación y reload.
5. Integrar en router (task-56).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Mantener `version` entera para migraciones futuras del schema.
- No poner API keys en el JSON; solo nombres de modelo si es necesario (también puede leerse de env).
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 `uv run pytest tests/agentes/test_meta_prompt.py` verde
- [ ] #2 `ruff check` sin errores nuevos
- [ ] #3 JSON legible y comentado en doc-003 (task-62) cómo editarlo con cuidado
<!-- DOD:END -->
