---
id: TASK-125
title: Hand requerir evidencia texto UC7 disparo contextual y edge cases
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
  - hand
milestone: m-1
dependencies:
  - TASK-123
  - TASK-124
references:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/requerir_evidencia.md
  - proyecto-3/src/hand/requerir_evidencia.py
  - proyecto-3/scripts/disparar_evidencia_hand.py
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
modified_files:
  - proyecto-3/src/hand/requerir_evidencia.py
  - proyecto-3/src/hand/__init__.py
  - proyecto-3/src/hand/recordatorio_postoperatorio.py
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/requerir_evidencia.md
  - proyecto-3/openfang/hands/taam_lili_hand/SKILL.md
  - proyecto-3/scripts/disparar_evidencia_hand.py
  - proyecto-3/tests/hand/test_requerir_evidencia.py
  - proyecto-3/tests/fixtures/hand_evidencia_kv_ejemplo.json
  - proyecto-3/README.md
  - proyecto-3/docs/guion-demo-ruta-b.md
priority: medium
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC7 parcial (milestone m-1, Ruta B):** solicitar al paciente una **confirmacion escrita** por Telegram cuando el seguimiento lo indique; sin foto, audio ni video ([decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)). En el documento canonico del cliente, evidencias multimedia siguen **fuera de MVP**.

**Runtime:** Hand `taam_lili_hand` (`every_secs = 30` en demo), sesiones `telegram:{chat_id}`, memoria episodica = turnos en JSONL bajo `{OPENFANG_HOME}`, estado de solicitud en KV por sesion (`kv/hand_evidencia/{chat_id}.json`; en produccion mapeable a `evidencia:telegram:{chat_id}` en API OpenFang).

## Objetivo TASK-125

Adaptador Python **testeable** (`ejecutar_requerir_evidencia`, `procesar_respuesta_evidencia`) para disparo contextual, reintento 24 h, rechazo multimedia y auditoria `hand_evidencia.jsonl`, sin depender del LLM del Hand en pytest.

## Entregado por TASK-123 / TASK-124

Manifesto HAND, `listar_sesiones_activas`, recordatorio UC6 y `hand_recordatorio.jsonl`.

## Fuera de alcance

- Evidencias multimedia y almacenamiento clinico.
- OLTP de casos (`proyecto-2`).
- KV `escalado` y `debe_escalar()` → TASK-126.
- Ingesta de corpus.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 **Positivo:** con `pendiente_evidencia=true`, `ejecutar_requerir_evidencia()` envia solicitud con disclaimer; `procesar_respuesta_evidencia()` con texto valido persiste turno en JSONL y pone `pendiente_evidencia=false`
- [x] #2 **Negativo:** `es_indicio_multimedia` → `redactar_rechazo_multimedia()` enviado; pendiente sigue `true` (no cierra como evidencia valida)
- [x] #3 **Edge:** tras 24 h sin respuesta valida, maximo 1 reintento; tras otras 24 h post-reintento → `pendiente_evidencia=false`, `motivo_cierre=cierre_sin_respuesta`
- [x] #4 Playbook `requerir_evidencia.md` con pasos numerados y secciones **Negativo** (multimedia) y **Edge** (24 h / reintento)
- [x] #5 `uv run pytest tests/hand/test_requerir_evidencia.py tests/test_hand_taam_lili.py -q` verde (33 passed con recordatorio)
- [x] #6 **Disparo contextual:** hook opt-in `marcar_evidencia_tras_envio` en recordatorio UC6 documentado (adaptador Python, no LLM en CI)
- [x] #7 Auditoria `{OPENFANG_HOME}/audit/hand_evidencia.jsonl` con `tipo: hand_evidencia`
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Modulo [`proyecto-3/src/hand/requerir_evidencia.py`](../../proyecto-3/src/hand/requerir_evidencia.py): contrato KV, reintento, multimedia, ejecutar/procesar, auditoria.
2. Script [`proyecto-3/scripts/disparar_evidencia_hand.py`](../../proyecto-3/scripts/disparar_evidencia_hand.py).
3. Ampliar playbook, SKILL.md, README y guion demo.
4. Tests [`proyecto-3/tests/hand/test_requerir_evidencia.py`](../../proyecto-3/tests/hand/test_requerir_evidencia.py) + fixture KV.
5. Hook opcional en `ejecutar_recordatorio_postop(..., marcar_evidencia_tras_envio=False)`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**KV por sesion:** `pendiente_evidencia`, `ultimo_envio_iso`, `ultimo_reintento_iso`, `reintentos_evidencia` (max 1), `accion_solicitada`, `motivo_cierre`.

**Auditoria:** `{OPENFANG_HOME}/audit/hand_evidencia.jsonl` (`tipo: hand_evidencia`).

```bash
cd proyecto-3
uv run pytest tests/hand/test_requerir_evidencia.py tests/hand/test_recordatorio_postop.py tests/test_hand_taam_lili.py -q
uv run python scripts/disparar_evidencia_hand.py --solo-simular
uv run python scripts/disparar_recordatorio_hand.py --solo-simular --marcar-evidencia
```

**Cierre 2026-05-23:** modulo `src/hand/requerir_evidencia.py` (15 tests UC7); hook `marcar_evidencia_tras_envio` en recordatorio; scripts `disparar_evidencia_hand.py` y flag `--marcar-evidencia` en recordatorio.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Comportamiento UC7 documentado en SKILL.md (pytest + scripts)
- [x] #2 Pytest hand + estaticos verdes (33 passed, 2026-05-23)
- [x] #3 Tarea **Done** sin archivar (`task_complete`)
<!-- DOD:END -->
