---
id: TASK-126
title: Guardrails escalacion clinica palabras alarma chat y Hand disclaimer
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-23 17:17'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - hand
milestone: m-1
dependencies:
  - TASK-122
  - TASK-124
  - TASK-125
references:
  - proyecto-3/src/guardrails/escalacion_clinica.py
  - proyecto-3/openfang/hands/taam_lili_hand/HAND.toml
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/system.md
  - proyecto-3/src/hand/requerir_evidencia.py
  - proyecto-3/src/prompts/validar_hand.py
  - proyecto-3/tests/guardrails/test_palabras_alarma.py
  - proyecto-3/docs/checklist-pruebas-chat-fvl.md
  - proyecto-3/scripts/evaluar_guardrail_entrada.py
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
modified_files:
  - proyecto-3/src/guardrails/escalacion_clinica.py
  - proyecto-3/src/guardrails/__init__.py
  - proyecto-3/src/hand/requerir_evidencia.py
  - proyecto-3/src/hand/__init__.py
  - proyecto-3/src/prompts/validar_hand.py
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/system.md
  - proyecto-3/openfang/agents/bot_lili_taam/agent.toml
  - proyecto-3/tests/guardrails/test_palabras_alarma.py
  - proyecto-3/tests/hand/test_requerir_evidencia.py
  - proyecto-3/scripts/evaluar_guardrail_entrada.py
  - proyecto-3/docs/checklist-pruebas-chat-fvl.md
priority: high
ordinal: 1.953125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC-MVP-03 / UC8 (Ruta B):** ante red flags (dolor intenso, fiebre alta, sangrado abundante, dificultad respiratoria) el bot debe orientar **urgencias / medico tratante**, sin diagnosticar ni prescribir ([caso de uso](../../backlog/docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md) seccion 4, severidad `urgente`). En Ruta B no hay `alertas_triage` ni HITL en PostgreSQL; sustituto: **KV** `escalado=true` y auditoria `{OPENFANG_HOME}/audit/hand_escalacion.jsonl` ([decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)).

**Dependencias:** TASK-122 (prompt chat), TASK-124/125 (adaptadores Hand UC6/UC7).

## Objetivo TASK-126

Modulo Python **determinista** (`debe_escalar`, `marcar_escalacion`, mensaje de urgencia) integrado en entrada de Hands (UC7); chat reactivo sigue con prompt + pruebas manuales en checklist FVL.

## Fuera de alcance

- Panel staff, OLTP (`proyecto-2`), tool `clasificar_triage` con LLM.
- Deteccion por fiebre numerica sin frase «fiebre alta» (FVL-03 queda en prueba manual LLM).
- Interceptar respuestas del agente OpenFang en runtime (sin middleware Python en bridge Telegram).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 **Manual Telegram:** cada frase canonica del HAND.toml dispara orientacion de urgencias (4 frases literales)
- [x] #2 **pytest:** `debe_escalar("me duele un poco")` → `False`
- [x] #3 **pytest:** `redactar_mensaje_urgencia()` pasa `validar_mensaje_urgencia()` (disclaimer, sin dosis/prescripcion)
- [x] #4 **pytest:** tras `marcar_escalacion(...)`, KV `escalado=true` y linea en `audit/hand_escalacion.jsonl`
- [x] #5 **pytest:** parametrizado 4 frases canonicas → `True` y contraejemplos
- [x] #6 **pytest integracion:** `procesar_respuesta_evidencia` con alarma escala antes de cerrar evidencia
- [ ] #7 **Manual:** FVL-03 checklist (fiebre numerica) — comportamiento LLM, no substring deterministico
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. [`proyecto-3/src/guardrails/escalacion_clinica.py`](../../proyecto-3/src/guardrails/escalacion_clinica.py): `PALABRAS_ALARMA`, `debe_escalar`, KV, auditoria, `evaluar_entrada_usuario`.
2. Tests [`proyecto-3/tests/guardrails/test_palabras_alarma.py`](../../proyecto-3/tests/guardrails/test_palabras_alarma.py).
3. Hook en `procesar_respuesta_evidencia`; refactor `validar_hand.py`.
4. Script [`proyecto-3/scripts/evaluar_guardrail_entrada.py`](../../proyecto-3/scripts/evaluar_guardrail_entrada.py).
5. Actualizar `system.md`, sincronizar `agent.toml`, checklist TASK-126.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**KV por sesion:** `{OPENFANG_HOME}/kv/hand_escalacion/{chat_id}.json` — `escalado`, `frase_detectada`, `ultimo_disparo_iso`, `session_id`.

**Auditoria:** `{OPENFANG_HOME}/audit/hand_escalacion.jsonl` (`tipo: hand_escalacion`).

**Limitacion FVL-03:** «Tengo fiebre de 38,5 °C» no dispara `debe_escalar()` (requiere substring `fiebre alta`); el chat reactivo depende del prompt LLM.

```bash
cd proyecto-3
uv run pytest tests/guardrails/ tests/hand/test_requerir_evidencia.py tests/test_hand_taam_lili.py -q
uv run python scripts/evaluar_guardrail_entrada.py --texto "tengo sangrado abundante" --solo-simular
uv run python scripts/sincronizar_prompt_agente.py
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest tests/guardrails/ tests/hand/test_requerir_evidencia.py -q` verde
- [x] #2 Tarea **Done** sin archivar (AC manual #1 y #7 pendientes operador en Telegram)
<!-- DOD:END -->

## Final Summary

Modulo `src/guardrails/escalacion_clinica.py` con `debe_escalar`, KV `kv/hand_escalacion/`, auditoria `hand_escalacion.jsonl`, integracion en `procesar_respuesta_evidencia`, tests pytest (14 guardrails + integracion UC7), script `evaluar_guardrail_entrada.py`, checklist ESC-01..06 y prompt sincronizado. Pruebas manuales Telegram (#1, #7) quedan al operador.
