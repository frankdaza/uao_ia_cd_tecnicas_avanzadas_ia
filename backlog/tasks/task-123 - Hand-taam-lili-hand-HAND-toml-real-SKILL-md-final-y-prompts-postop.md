---
id: TASK-123
title: Hand taam lili hand HAND toml real SKILL md final y prompts postop
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-23 16:57'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - hand
milestone: m-1
dependencies:
  - TASK-119
references:
  - proyecto-3/openfang/hands/taam_lili_hand/HAND.toml
  - proyecto-3/openfang/hands/taam_lili_hand/SKILL.md
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
modified_files:
  - proyecto-3/openfang/hands/taam_lili_hand/HAND.toml
  - proyecto-3/openfang/hands/taam_lili_hand/SKILL.md
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/recordatorio_postop.md
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/requerir_evidencia.md
  - proyecto-3/src/prompts/validar_hand.py
  - proyecto-3/tests/test_hand_taam_lili.py
  - proyecto-3/README.md
  - proyecto-3/docs/guion-demo-ruta-b.md
priority: high
ordinal: 15.625
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Hand autonomo **taam_lili_hand** (Ruta B): recordatorios postoperatorios (UC6) y solicitud de evidencia en texto (UC7 parcial). TASK-119 entrego HAND instalable; TASK-122 fijo `prompts/system.md` y sincronizacion a `agent.toml`.

## Objetivo TASK-123

Manifesto del Hand **versionable y verificable sin red**: `HAND.toml` (schedule demo cada 30 s), `SKILL.md`, seccion `[prompts]` enlazada a playbooks en `prompts/`, alineado a [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md).

## Fuera de alcance

Logica de envio cron, mocks de sesiones, KV `pendiente_evidencia`, `debe_escalar()` → TASK-124, TASK-125, TASK-126.

## Schedule

**Canon en repo:** `[schedule] every_secs = 30` y `tz = "America/Bogota"` para demo y desarrollo. Un cron matutino (decision-8) queda como mejora futura, no criterio de cierre de esta tarea.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `[schedule]` con `every_secs = 30` (entero) y `tz = "America/Bogota"`; `[capabilities]` activas; `[guardrails]` con `no_diagnostico`, `disclaimer_obligatorio`, `escalar_palabras_alarma`
- [x] #2 `[prompts]` referencia `recordatorio_postop.md` y `requerir_evidencia.md`; archivos existen (pytest)
- [x] #3 `SKILL.md`: Telegram, intervalo 30 s, UC6/UC7, limites MVP, enlace a `prompts/`
- [x] #4 `uv run pytest tests/test_hand_taam_lili.py -q` verde (8 tests)
- [ ] #5 `openfang hand list` / `hand activate` exitoso — requiere daemon (`openfang start`); ver Implementation Notes
- [x] #6 **Negativo:** TOML invalido impide parseo — cubierto por `tomllib` + `validar_hand_manifest` en pytest
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Completar `HAND.toml`: `[prompts]`, guardrails alineados TASK-126, mantener `every_secs = 30`.
2. Ampliar `SKILL.md` y playbooks (`recordatorio_postop`, `requerir_evidencia`).
3. `src/prompts/validar_hand.py` + `tests/test_hand_taam_lili.py`.
4. README y `docs/guion-demo-ruta-b.md` (intervalo 30 s, coste API, desactivar Hand).
5. Smoke CLI `hand install` / `list` / `activate`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```toml
[schedule]
every_secs = 30
tz = "America/Bogota"

[prompts]
recordatorio_postoperatorio = "prompts/recordatorio_postop.md"
requerir_evidencia_texto = "prompts/requerir_evidencia.md"

[guardrails]
escalar_palabras_alarma = [
  "dolor intenso",
  "fiebre alta",
  "sangrado abundante",
  "dificultad respiratoria",
]
```

```bash
cd proyecto-3
uv run pytest tests/test_hand_taam_lili.py -q
openfang hand install openfang/hands/taam_lili_hand
openfang hand list
openfang hand activate taam_lili_hand
```

**Cierre (2026-05-23):** Manifesto con `[prompts]`, `every_secs = 30`, guardrails alineados TASK-126. `validar_hand.py` + 8 tests. Smoke CLI #5 pendiente de daemon en esta sesion (`openfang hand list` reporto daemon no activo).
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 pytest Hand verde + manifesto completo
- [x] #2 Hand activable en demo (comandos documentados en README/SKILL; activar tras `openfang start`)
- [x] #3 Tarea **Done** sin archivar
<!-- DOD:END -->
