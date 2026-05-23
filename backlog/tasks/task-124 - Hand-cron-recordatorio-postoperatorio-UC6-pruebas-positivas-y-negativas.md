---
id: TASK-124
title: 'Hand cron recordatorio postoperatorio UC6 pruebas positivas y negativas'
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
  - TASK-122
  - TASK-123
references:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/recordatorio_postop.md
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
modified_files:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/recordatorio_postop.md
  - proyecto-3/tests/hand/test_recordatorio_postop.py
priority: high
ordinal: 1240
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC6 cubierto:** recordatorio proactivo postoperatorio vía Hand cron. Playbook en `recordatorio_postop.md` con pruebas positivas, negativas y edge documentadas en código de prueba.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 **Positivo:** con ≥1 sesión Telegram activa, el Hand envía mensaje con disclaimer y sin inventar dosis
- [ ] #2 **Negativo:** sin sesiones activas → `enviados == 0`, log `sin_sesiones_activas`
- [ ] #3 **Edge:** sesión sin contexto reciente → mensaje genérico de autocuidado, sin datos clínicos inventados
- [ ] #4 Entrada de auditoría visible en dashboard/JSONL (`tipo=hand_recordatorio`)
- [ ] #5 Test `test_recordatorio_sin_sesiones_no_envia` pasa con mock
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Finalizar prompt `recordatorio_postop.md`.
2. Implementar adaptador testeable `ejecutar_recordatorio_postop()` si OpenFang no expone hook directo.
3. Forzar ejecución manual: `openfang hand run taam_lili_hand --playbook recordatorio_postop` (comando según CLI real).
4. Escribir tests pytest con monkeypatch.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```python
def test_recordatorio_sin_sesiones_no_envia(monkeypatch):
    monkeypatch.setattr(
        "hand_taam.memoria.listar_sesiones_activas", lambda: []
    )
    resultado = ejecutar_recordatorio_postop()
    assert resultado.enviados == 0
    assert resultado.motivo == "sin_sesiones_activas"
```

```markdown
## Objetivo (recordatorio_postop.md)
Enviar recordatorio amable de signos de alarma y adherencia a indicaciones generales.
Nunca indicar mg/ml ni cambiar medicacion.
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Prueba manual o cron documentada
- [ ] #2 Tests unitarios verdes
- [ ] #3 Tarea **Done** sin archivar
<!-- DOD:END -->
