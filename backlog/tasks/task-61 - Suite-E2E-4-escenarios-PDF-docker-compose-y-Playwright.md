---
id: TASK-61
title: Suite E2E de los 4 escenarios del PDF (pytest + httpx y Playwright frontend)
status: To Do
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-11 00:00'
labels:
  - e2e
  - docker
  - modulo-2
dependencies:
  - TASK-60
  - TASK-59
references:
  - tests/e2e/test_escenarios_modulo2.py
  - frontend/tests/e2e/
  - scripts/README.md
  - docker-compose.yml
documentation:
  - backlog/docs/actividades/Técnicas Avanzadas de IA en Modelos de Lenguaje - Actividad del Módulo 2.pdf
priority: high
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El PDF del Módulo 2 define escenarios de validación agéntica. Se requiere una suite **E2E** reproducible contra API levantada con **docker-compose**, más specs **Playwright** en el frontend equivalentes cuando aplique.

## Objetivo

1. Crear **`tests/e2e/test_escenarios_modulo2.py`** usando `pytest` + `httpx` contra `BASE_URL` configurable:

   - **(a) RAG**: pregunta abierta sobre la fundación que fuerce `rag_denso` y verifique presencia de `EventoFuentes` o metadata coherente.
   - **(b) Memoria**: secuencia de dos turnos donde el segundo dependa del primero (p. ej. referencia anafórica); verificar continuidad en respuesta o en eventos.
   - **(c) Structured tool**: pregunta tipo horario/contacto que fuerce `faq_estructurada`.
   - **(d) Mixto**: conversación en un mismo `session_id` combinando (a)(b)(c); verificar `tool_decidida` por turno vía eventos `pensamiento`/`herramienta`.

2. Cada escenario debe **assert** sobre la tool esperada (tolerancia documentada ante variabilidad del LLM real; si es inestable, usar modo `MOCK_LLM=1` documentado).

3. **Frontend**: añadir/actualizar specs en `frontend/tests/e2e/` para login + chat mínimo reflejando escenarios críticos.

4. Documentar en **`scripts/README.md`** cómo levantar compose, exportar `OPENAI_API_KEY`, poblar Qdrant (`indexar_corpus_qdrant.py`) y ejecutar `uv run pytest tests/e2e/ ...`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 Archivo `tests/e2e/test_escenarios_modulo2.py` implementa los cuatro escenarios nombrados
- [ ] #2 Variables de entorno documentadas (`BASE_URL`, claves, flags mock)
- [ ] #3 Playwright cubre al menos login + una pregunta FAQ y una abierta (si LLM real inestable, usar intercept/stub de API)
- [ ] #4 `scripts/README.md` incluye comandos copy-paste para reproducir
- [ ] #5 Los tests se saltan con mensaje claro si faltan servicios/credenciales
- [ ] #6 No se commitean secretos ni `.env` reales
- [ ] #7 Resultados agregados referenciables desde informe LaTeX (task-63)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Definir fixtures e2e con session autenticada vía `POST /api/sesiones`.
2. Implementar helpers para consumir SSE hasta `EventoFinal`.
3. Codificar aserciones por escenario y datos semilla mínimos en Qdrant.
4. Añadir job opcional en CI (manual `workflow_dispatch`) si costo lo impide.
5. Escribir guía en `scripts/README.md` y enlazar desde README principal en task-63.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Para CI estable, preferir contenedor con respuestas mock del LLM (feature flag en backend) además del modo OpenAI real local del equipo.
- Tiempos de espera SSE deben ser generosos pero con timeout global.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 `uv run pytest tests/e2e/test_escenarios_modulo2.py` pasa en entorno del equipo con compose + clave válida **o** modo mock documentado
- [ ] #2 `pnpm --dir frontend exec playwright test` pasa en configuración documentada
- [ ] #3 Documentación en `scripts/README.md` revisada en español latinoamericano
<!-- DOD:END -->
