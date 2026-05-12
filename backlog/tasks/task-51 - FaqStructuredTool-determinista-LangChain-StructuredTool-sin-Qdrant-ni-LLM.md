---
id: TASK-51
title: FaqStructuredTool determinista (LangChain StructuredTool) sin Qdrant ni LLM
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-12 06:47'
labels:
  - langchain
  - herramientas
  - modulo-2
dependencies:
  - TASK-50
references:
  - src/agentes/herramientas/faq_tool.py
  - src/api/configuracion.py
  - tests/agentes/test_faq_tool.py
documentation:
  - .claude/skills/llm-backend/SKILL.md
priority: high
ordinal: 0.00048828125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El router necesita una herramienta **100 % determinista** que resuelva intents de FAQ mediante el archivo `data/structured/faqs.json`, **sin** tocar Qdrant, **sin** embeddings y **sin** invocar LLM dentro de la tool.

## Objetivo

Implementar `src/agentes/herramientas/faq_tool.py`:

1. Función interna `buscar_faq(consulta: str) -> FaqRespuesta | None` (tipos en español ASCII o dataclass):
   - Normalizar consulta: `lower`, `unicodedata.normalize('NFKD')` para quitar tildes, tokenización por límites de palabra (`regex`).
   - Para cada FAQ, calcular **score por solapamiento** de `keywords` (p. ej. Jaccard, ratio de keywords encontradas, etc. — documentar fórmula brevemente).
   - Retornar el mejor match si `score >= FAQ_UMBRAL_MATCH` (default **0.5** desde settings); si no, `None`.

2. Exponer `crear_faq_tool() -> StructuredTool` de LangChain con:
   - `name="faq_estructurada"`
   - `description` clara para el modelo router (español en string UI/prompt).

3. **Prohibido** importar `src/retrieval/recuperador.py` o cualquier código BM25.

## Tests

Cobertura: cada FAQ con una frase que debería matchear; casos negativos con preguntas abiertas de dominio médico que deben **fallar** el umbral y devolver `None`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `crear_faq_tool()` retorna `StructuredTool` invocable por LangGraph
- [x] #2 Matching determinista; mismas entradas producen misma salida
- [x] #3 Umbral `FAQ_UMBRAL_MATCH` configurable por `.env` / settings
- [x] #4 No hay imports de Qdrant, LlamaIndex ni OpenAI en este módulo
- [x] #5 Tests cubren ≥1 caso positivo por FAQ y ≥3 negativos
- [x] #6 Manejo de archivo JSON ausente con error controlado y mensaje en español
- [x] #7 Docstring describe la función de scoring
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Definir modelos Pydantic/dataclass `FaqEntrada`, `FaqRespuesta`.
2. Cargar JSON una vez (caché en módulo) con invalidación opcional por `mtime`.
3. Implementar normalización y scoring.
4. Envolver en `StructuredTool.from_function` o API equivalente LC v1.
5. Añadir suite pytest dedicada.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Evitar cargar el JSON en cada request si el costo importa; usar `lru_cache` o singleton por proceso.
- Si el score es empate, preferir FAQ con más keywords coincidentes o orden estable por `id`.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado `src/agentes/herramientas/faq_tool.py`: `buscar_faq` con normalización NFKD + minúsculas, tokens alfanuméricos, score = palabras clave coincidentes / total por FAQ, umbral `FAQ_UMBRAL_MATCH` vía `Configuracion.faq_umbral_match`, cache por `mtime` del JSON, empate por score/coincidencias/`id`. `crear_faq_tool()` expone `StructuredTool` `faq_estructurada`. Ruta JSON configurable con `FAQ_JSON_RELATIVO_RAIZ` (default `data/structured/faqs.json` relativo a la raíz del repo). Ausencia de archivo: `ArchivoFaqStructuredAusenteError` con mensaje en español. Tests en `tests/agentes/test_faq_tool.py` (1 positivo por FAQ, negativos médicos, umbral, archivo ausente, invoke). Ejemplo manual: `uv run python -c 'from src.agentes.herramientas.faq_tool import crear_faq_tool; print(crear_faq_tool().invoke({"consulta": "telefono PBX 602 331 9090"}))'`
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest` verde para tests de `FaqStructuredTool`
- [x] #2 `ruff check` sin errores nuevos
- [x] #3 Ejemplo de invocación manual documentado en notas o doc-003
<!-- DOD:END -->
