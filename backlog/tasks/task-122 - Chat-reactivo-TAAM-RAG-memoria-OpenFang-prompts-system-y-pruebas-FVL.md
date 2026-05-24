---
id: TASK-122
title: Chat reactivo TAAM RAG memoria OpenFang prompts system y pruebas FVL
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-24 16:36'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
milestone: m-1
dependencies:
  - TASK-120
  - TASK-121
references:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/system.md
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
modified_files:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/system.md
  - proyecto-3/openfang/agents/bot_lili_taam/agent.toml
  - proyecto-3/docs/checklist-pruebas-chat-fvl.md
  - proyecto-3/scripts/sincronizar_prompt_agente.py
  - proyecto-3/scripts/contar_memorias_semanticas.py
  - proyecto-3/scripts/arrancar_dev.sh
  - proyecto-3/src/prompts/validar.py
  - proyecto-3/tests/test_prompt_bot_lili.py
  - proyecto-3/tests/test_checklist_chat_fvl.py
  - proyecto-3/tests/test_sincronizar_prompt_agente.py
  - proyecto-3/README.md
priority: high
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC8 (milestone m-1):** chat reactivo del paciente por Telegram con **RAG** sobre memoria semántica OpenFang (equivalente simplificado de UC-MVP-03 Ruta A, sin OLTP ni HITL).

**Dependencias:** TASK-121 (ingesta corpus) **Done**; TASK-120 (Telegram operativo).

**Prompt canónico:** [`proyecto-3/openfang/hands/taam_lili_hand/prompts/system.md`](../../proyecto-3/openfang/hands/taam_lili_hand/prompts/system.md). El chat en vivo usa [`agent.toml`](../../proyecto-3/openfang/agents/bot_lili_taam/agent.toml) → sincronizar con `scripts/sincronizar_prompt_agente.py` (también en `arrancar_dev.sh`).

**Fuera de alcance aquí:** guardrails KV y `debe_escalar()` → TASK-126 (solo instrucciones de alarma en el prompt).

**Skill:** `qa-prompt-engineering`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Tras ingesta, las 5 preguntas FVL del checklist por categoría responden con referencia al corpus: **cuidados** (FVL-01), **medicación** (FVL-02), **signos alarma** (FVL-03), **dieta** (FVL-04), **actividad** (FVL-05) — *validar en Telegram tras ingesta real*
- [ ] #1b Pregunta fuera de corpus (FVL-06: «¿Cuál es el precio del dólar hoy?») responde con honestidad sin inventar protocolo clínico — *validar en Telegram*
- [x] #2 Cada respuesta clínica incluye disclaimer verificable (contiene *no reemplaza* y *médico tratante*) — *codificado en `system.md` + tests*
- [ ] #3 **Negativo:** sin ingesta previa (DB sin `memories` semánticas), la respuesta no afirma protocolos o dosis específicas inventadas (procedimiento en checklist) — *validar en Telegram*
- [ ] #4 Evidencia: extracto `openfang sessions --json` o JSONL anonimizado en `proyecto-3/docs/checklist-pruebas-chat-fvl.md` — *plantilla lista; pegar tras demo*
- [x] #6 `system.md` y `agent.toml` comparten el mismo `system_prompt` (pytest `test_prompt_bot_lili.py`)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Redactar `system.md` (RAG, citas, disclaimer, límites, alarma ligera).
2. `uv run python scripts/sincronizar_prompt_agente.py` → `agent.toml`; hook en `arrancar_dev.sh`.
3. Crear `docs/checklist-pruebas-chat-fvl.md` y `scripts/contar_memorias_semanticas.py`.
4. Ingesta + pruebas Telegram FVL-01..06; documentar evidencia en checklist.
5. `uv run pytest` tests estáticos de prompt y checklist.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Tabla FVL en [`proyecto-3/docs/checklist-pruebas-chat-fvl.md`](../../proyecto-3/docs/checklist-pruebas-chat-fvl.md).

Comandos:

```bash
cd proyecto-3
uv run python scripts/sincronizar_prompt_agente.py
uv run python ingesta/indexar_corpus_openfang.py --permitir-db-en-vivo
uv run python scripts/contar_memorias_semanticas.py --exigir-ingesta
./scripts/arrancar_dev.sh
uv run pytest tests/test_prompt_bot_lili.py tests/test_checklist_chat_fvl.py tests/test_sincronizar_prompt_agente.py -q
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Checklist documentado (`docs/checklist-pruebas-chat-fvl.md`); ejecucion Telegram pendiente operador
- [x] #2 Tarea **Done** sin archivar
<!-- DOD:END -->

## Final Summary

Prompt Bot Lili unificado: `system.md` canónico con RAG estricto, citas, disclaimer y señales de alarma; sincronización a `agent.toml` vía `scripts/sincronizar_prompt_agente.py` (integrado en `arrancar_dev.sh`). Módulo `src/prompts/validar.py` y 12 tests pytest. Checklist FVL y `contar_memorias_semanticas.py` listos. AC #1, #1b, #3, #4 requieren prueba manual en Telegram tras ingesta (`memorias_semanticas=0` en entorno de implementación).
