---
id: TASK-123
title: 'Hand taam lili hand HAND toml real SKILL md final y prompts postop'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
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
modified_files:
  - proyecto-3/openfang/hands/taam_lili_hand/HAND.toml
  - proyecto-3/openfang/hands/taam_lili_hand/SKILL.md
priority: high
ordinal: 1230
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El Hand **taam_lili_hand** es el playbook autónomo de Ruta B (recordatorios + evidencia texto). `HAND.toml` y `SKILL.md` están en placeholder; deben alinearse con decision-8 y prompts en `prompts/`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `HAND.toml` define cron `0 8 * * *`, capabilities y guardrails `palabras_alarma`
- [ ] #2 `openfang hand list` muestra `taam_lili_hand`; `openfang hand activate taam_lili_hand` exitoso
- [ ] #3 `SKILL.md` documenta capacidades, límites MVP y canal default Telegram
- [ ] #4 **Negativo:** TOML inválido impide activación — corregir antes de Done
- [ ] #5 Prompts `recordatorio_postop.md` y `requerir_evidencia.md` referenciados desde HAND
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Completar `[hand]`, `[schedule]`, `[capabilities]`, `[guardrails]`, `[channel]`.
2. Ampliar SKILL.md.
3. Smoke CLI hand list/activate.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```toml
[hand]
name = "taam_lili_hand"
description = "Seguimiento postoperatorio TAAM - Fundacion Valle del Lili"

[schedule]
cron = "0 8 * * *"

[capabilities]
recordatorio_postoperatorio = true
requerir_evidencia_texto = true

[guardrails]
palabras_alarma = [
  "dolor intenso",
  "fiebre alta",
  "sangrado abundante",
  "dificultad respiratoria",
]

[channel]
default = "telegram"
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Hand activable en demo
- [ ] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
