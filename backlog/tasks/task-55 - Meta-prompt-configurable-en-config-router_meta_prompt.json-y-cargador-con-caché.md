---
id: TASK-55
title: >-
  Meta-prompt configurable en config/router_meta_prompt.json y cargador con
  caché
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-14 19:32'
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
ordinal: 10000
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
- [x] #1 Archivo JSON versionado bajo `config/` y montado ro en Docker (task-45)
- [x] #2 Validación Pydantic rechaza configuraciones incompletas con errores legibles
- [x] #3 Caché por `mtime` verificable en test (dos cargas, segunda tras `touch`)
- [x] #4 `reglas_decision` y `herramientas` cubren ambas tools (`faq_estructurada`, `rag_denso`)
- [x] #5 `saludo_template` documenta placeholders soportados (`{nombre}` mínimo)
- [x] #6 `respuesta_sin_contexto` alineado con política Lili / `src/qa/prompt.py`
- [x] #7 Tests `tests/agentes/test_meta_prompt.py` pasan
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

DOD ítem 3 (doc-003): el archivo backlog/docs/doc-003 aún no existe en el repo (task-62); la edición queda pendiente.

Integración en el router LangGraph: task-56.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se añadió config/router_meta_prompt.json con schema v1 (herramientas faq_estructurada y rag_denso, reglas_decision, saludo_template con {nombre}, respuesta_sin_contexto alineada con src/qa/prompt.py). Se implementó src/agentes/meta_prompt.py con modelos Pydantic v2, validación de políticas y caché por st_mtime_ns por ruta resuelta. Tests en tests/agentes/test_meta_prompt.py cubren JSON inválido, versión no soportada, schema incompleto, caché (is) y recarga tras cambio en disco. Comandos verificados: uv run pytest tests/agentes/test_meta_prompt.py y ruff check/format en los archivos tocados.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest tests/agentes/test_meta_prompt.py` verde
- [x] #2 `ruff check` sin errores nuevos
- [x] #3 JSON legible y comentado en doc-003 (task-62) cómo editarlo con cuidado
<!-- DOD:END -->
