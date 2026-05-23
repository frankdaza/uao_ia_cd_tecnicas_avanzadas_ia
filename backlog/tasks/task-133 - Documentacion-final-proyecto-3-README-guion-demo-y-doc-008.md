---
id: TASK-133
title: 'Documentacion final proyecto-3 README guion demo y doc-008'
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
  - TASK-131
  - TASK-132
references:
  - proyecto-3/README.md
  - proyecto-3/docs/guion-demo-ruta-b.md
  - backlog/docs/doc-008 - Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md
  - backlog/decisions/decision-8 - Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - backlog/milestones/m-1 - taam-ruta-b-openfang.md
modified_files:
  - proyecto-3/README.md
  - proyecto-3/docs/guion-demo-ruta-b.md
  - backlog/docs/doc-008 - Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md
priority: high
ordinal: 1330
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Cierre documental de Ruta B: README operativo, guion demo 15 min con tiempos verificados, comparativa **Ruta A vs B**, y guía **`doc-008`** en `backlog/docs/` (skill `backlog-docs`).

**No** incluye informe PDF unificado (descartado en planificación).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `proyecto-3/README.md`: instalación OpenFang, `uv sync`, `arrancar_dev.sh`, ingesta, Telegram, t-SNE, fallback Ollama
- [ ] #2 `docs/guion-demo-ruta-b.md`: tabla minuto a minuto (0–15), checklist pre-demo, comandos exactos
- [ ] #3 `backlog/docs/doc-008 - Arquitectura-M3-TAAM-Ruta-B-OpenFang-Proyecto-3.md` con front matter `id: doc-008`, `type: architecture`, diagramas mermaid, mapeo UC, guardrails
- [ ] #4 Sección comparativa A (`proyecto-2`) vs B (`proyecto-3`) sin contradecir decision-7/8
- [ ] #5 **Negativo:** ningún secreto ni token en docs; solo placeholders
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
Front matter doc-008:

```yaml
---
id: doc-008
title: doc-008 - Arquitectura M3 TAAM Ruta B OpenFang Proyecto 3
type: architecture
created_date: '2026-05-22'
---
```

Guion demo (fragmento tabla):

| Min | Actividad |
| --- | --- |
| 0-2 | Contexto: paralelo Ruta A vs B, ADR decision-8 |
| 3-5 | Dashboard OpenFang + memoria 6 capas |
| 6-8 | Ingesta corpus + RAG en Telegram |
| 9-11 | Hand cron / evidencia texto |
| 12-15 | Notebook t-SNE + preguntas |

**Skill:** `backlog-docs`, `backlog-md`.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 doc-008 y README revisados en español latinoamericano
- [ ] #2 Enlaces relativos válidos a decision-8 y m-1
- [ ] #3 Tarea **Done** sin archivar
<!-- DOD:END -->
