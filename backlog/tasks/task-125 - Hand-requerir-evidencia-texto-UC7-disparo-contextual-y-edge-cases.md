---
id: TASK-125
title: 'Hand requerir evidencia texto UC7 disparo contextual y edge cases'
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
  - TASK-123
  - TASK-124
references:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/requerir_evidencia.md
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
modified_files:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/requerir_evidencia.md
  - proyecto-3/tests/hand/test_requerir_evidencia.py
priority: medium
ordinal: 1250
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC7 parcial:** solicitar evidencia al paciente en **texto** (MVP Ruta B). Disparo vía flag `pendiente_evidencia` en Structured KV o palabra clave del playbook tras recordatorio.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 **Positivo:** Hand pide confirmación escrita y persiste respuesta en memoria episódica
- [ ] #2 **Negativo:** paciente envía indicio de foto/audio → respuesta indicando que MVP solo acepta texto
- [ ] #3 **Edge:** sin respuesta en 24h → máximo 1 reintento; luego `pendiente_evidencia=false` en KV
- [ ] #4 Plantilla en `requerir_evidencia.md` con pasos numerados
- [ ] #5 Tests cubren los tres escenarios con mocks
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Definir contrato KV: `pendiente_evidencia`, `ultimo_reintento_iso`.
2. Completar prompt y lógica de reintento.
3. Prueba Telegram end-to-end opcional.
4. Tests pytest.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```python
def debe_reintentar_evidencia(kv: dict, ahora_iso: str) -> bool:
    if not kv.get("pendiente_evidencia"):
        return False
    if kv.get("reintentos_evidencia", 0) >= 1:
        return False
    # comparar ultimo_reintento + 24h con ahora_iso
    return True
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Comportamiento documentado en SKILL.md
- [ ] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
