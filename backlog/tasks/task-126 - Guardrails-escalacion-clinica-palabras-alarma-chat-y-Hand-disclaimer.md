---
id: TASK-126
title: Guardrails escalacion clinica palabras alarma chat y Hand disclaimer
status: In Progress
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-23 17:11'
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
references:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/system.md
  - proyecto-3/openfang/hands/taam_lili_hand/HAND.toml
  - proyecto-3/tests/guardrails/test_palabras_alarma.py
modified_files:
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/system.md
  - proyecto-3/openfang/hands/taam_lili_hand/prompts/recordatorio_postop.md
  - proyecto-3/tests/guardrails/test_palabras_alarma.py
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Guardrails clínicos: ante palabras de alarma el bot debe **escalar** (urgencias / médico tratante), registrar `escalado=true` en KV y **no** diagnosticar ni prescribir. Aplica a chat reactivo y mensajes del Hand.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Cada palabra del set (`dolor intenso`, `fiebre alta`, `sangrado abundante`, `dificultad respiratoria`) dispara mensaje de urgencia en prueba manual
- [ ] #2 **Negativo:** «me duele un poco» sin calificativo de alarma **no** escala
- [ ] #3 **Regresión:** respuesta no contiene diagnóstico ni prescripción de fármacos
- [ ] #4 KV `escalado=true` tras escalación (verificable en dashboard o test mock)
- [ ] #5 Tests automatizados por frase de alarma y contraejemplo
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Centralizar lista `PALABRAS_ALARMA` en módulo compartido o duplicar en prompts con misma lista que HAND.toml.
2. Actualizar `system.md` y `recordatorio_postop.md`.
3. Suite pytest `test_palabras_alarma.py` con función pura `debe_escalar(texto) -> bool`.
4. Pruebas Telegram con frases UC.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```python
PALABRAS_ALARMA = (
    "dolor intenso",
    "fiebre alta",
    "sangrado abundante",
    "dificultad respiratoria",
)

def debe_escalar(texto: str) -> bool:
    t = texto.lower()
    return any(p in t for p in PALABRAS_ALARMA)

MENSAJE_URGENCIA = (
    "Por sus sintomas, acuda de inmediato a urgencias o contacte a su medico tratante. "
    "Este bot no puede atender emergencias."
)
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Tests verdes
- [ ] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
