---
id: TASK-127
title: 'Dashboard OpenFang historial sesiones y JSONL UC4 parcial consulta'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - docs
milestone: m-1
dependencies:
  - TASK-122
references:
  - proyecto-3/docs/dashboard-openfang.md
  - proyecto-3/openfang/openfang.toml
modified_files:
  - proyecto-3/docs/dashboard-openfang.md
priority: medium
ordinal: 1270
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC4 parcial:** sin panel React TAAM, la consulta de seguimiento se demuestra con el **dashboard OpenFang** (`:4200`) y archivos **JSONL** bajo `OPENFANG_HOME`. Documentar procedimiento para sustentación.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `docs/dashboard-openfang.md` explica navegación UI, ubicación JSONL y ejemplo `jq` por `session_id`
- [ ] #2 Demo reproducible: hilo de paciente de prueba + entrada de Hand visible
- [ ] #3 **Negativo:** `OPENFANG_HOME` inexistente → doc indica crear directorio y reiniciar OS
- [ ] #4 Capturas o descripciones sin PHI real (datos ficticios)
- [ ] #5 Comando ejemplo: `jq 'select(.session_id=="telegram:111111111")' sessions.jsonl`
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Generar tráfico de prueba (tasks 122/124).
2. Explorar dashboard y exportar rutas reales de logs.
3. Redactar doc con troubleshooting.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```bash
export OPENFANG_HOME=proyecto-3/openfang/data
jq -c 'select(.session_id | startswith("telegram:"))' \
  "$OPENFANG_HOME/logs/sessions.jsonl" | head
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Doc en español
- [ ] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
