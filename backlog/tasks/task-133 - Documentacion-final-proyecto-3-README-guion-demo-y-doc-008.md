---
id: TASK-133
title: Documentacion final proyecto-3 README guion demo y doc-008
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-24 17:14'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - docs
milestone: m-1
dependencies:
  - TASK-131
  - TASK-132
references:
  - proyecto-3/README.md
  - proyecto-3/docs/guion-demo-ruta-b.md
  - backlog/docs/doc-008 - Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - backlog/milestones/m-1 - taam-ruta-b-openfang.md
modified_files:
  - proyecto-3/README.md
  - proyecto-3/docs/guion-demo-ruta-b.md
  - backlog/docs/doc-008 - Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Cierre documental de Ruta B: README operativo, guion demo 15 min con tiempos verificados, comparativa **Ruta A vs B**, y guía **`doc-008`** en `backlog/docs/` (skill `backlog-docs`).

**No** incluye informe PDF unificado (descartado en planificación).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `proyecto-3/README.md`: instalación OpenFang, `uv sync`, `arrancar_dev.sh`, ingesta, Telegram, t-SNE, fallback Ollama
- [x] #2 `docs/guion-demo-ruta-b.md`: tabla minuto a minuto (0–15), checklist pre-demo, comandos exactos
- [x] #3 `backlog/docs/doc-008 - Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md` con front matter `id: doc-008`, `type: architecture`, diagramas mermaid, mapeo UC, guardrails
- [x] #4 Sección comparativa A (`proyecto-2`) vs B (`proyecto-3`) sin contradecir decision-7/8
- [x] #5 **Negativo:** ningún secreto ni token en docs; solo placeholders
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Actualizar README con enlaces a tasks completadas y milestone m-1.
2. Validar guion contra demo real (task-131).
3. Crear doc-008 siguiendo `backlog-docs` skill (nombre `doc-008 - Slug.md`).
4. Enlazar doc-008 desde milestone m-1 y decision-8 si aplica.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Guion: tabla canonica 0-2 / 3-5 / 6-8 / 9-11 / 12-15 (sustituye desfase 0-2 / 2-5 / 5-8 del borrador anterior). Sin tests pytest (decision del equipo).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Creado backlog/docs/doc-008 con arquitectura Ruta B (mermaid, UC, guardrails, comparativa A vs B). README proyecto-3: seccion Ruta A vs B y referencias m-1/doc-008/guion. guion-demo-ruta-b.md: checklist tabular, tabla 15 min con comandos, bloque comandos de referencia. Enlaces cruzados en m-1, decision-8 y doc-004.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 doc-008 y README revisados en español latinoamericano
- [x] #2 Enlaces relativos válidos a decision-8 y m-1
- [x] #3 Tarea **Done** sin archivar
<!-- DOD:END -->
