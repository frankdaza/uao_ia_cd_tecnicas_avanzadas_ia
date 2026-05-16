---
id: TASK-92
title: >-
  Cierre documental: nucleo vs laboratorio, diagrama doc-003 y README
  post-migracion
status: In Progress
assignee:
  - Frank Daza
created_date: '2026-05-16 16:50'
updated_date: '2026-05-16 17:26'
labels:
  - migracion
  - clean-architecture
  - modulo-2
  - documentacion
  - cierre
dependencies:
  - TASK-86
  - TASK-87
  - TASK-88
  - TASK-90
references:
  - README.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
  - src/rag/
  - src/laboratorio/
documentation:
  - >-
    backlog/decisions/decision-6 -
    Migracion-Incremental-Clean-Architecture-M2.md
  - backlog/docs/doc-004 - Estudio-Migracion-Clean-Architecture.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Mitigacion en decision-6: actualizar doc-003 con tabla nucleo vs laboratorio cuando exista reorganizacion rag; cierre narrativo para auditores.

## Objetivo

Sincronizar documentacion operativa con el layout real del repo despues de tasks de codigo, y reflejar resumen en README.

## Dependencias logicas

Debe ejecutarse cuando rag runtime/evaluacion, retiro app, documentacion qa inicial y reglas estables esten listos; puede mencionar task-89 si aun no aplica.

## Entregables

- Edits en doc-003 (diagrama + tabla + texto puente).
- Edits acotados en README (seccion arquitectura o indice de carpetas).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 doc-003 incluye diagrama Mermaid de limites alineado a decision-6 (Presentacion HTTP, Orquestacion agente, infra rag runtime/evaluacion, laboratorio).
- [ ] #2 doc-003 incluye tabla canonica modulo -> categoria (nucleo M2 / laboratorio / scripts / infra OLTP).
- [ ] #3 README.md refleja arbol conceptual post-migracion: rag/runtime, rag/evaluacion; ausencia de src/app; nota sobre qa segun estado (src/qa vs laboratorio/qa_legacy si task-89 ya cerro).
- [ ] #4 Front matter de doc-003 tiene updated_date coherente con el cambio sustancial.
- [ ] #5 `uv run pytest` no es obligatorio en tarea solo-doc; si se toca README sin codigo, indicar N/A en notas de cierre.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Verificar en working tree el layout real (`tree -L 3 src/rag` o listado manual).
2. Actualizar doc-003: diagrama + tabla nucleo vs laboratorio + texto de transicion desde estado previo.
3. Ajustar README: reflejar carpetas clave y enlazar doc-003.
4. `updated_date` en doc-003.
5. Revision cruzada con decision-6 y doc-004 (terminos nucleo/laboratorio).
6. Cerrar tarea.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Reutilizar/adaptar el Mermaid de decision-6; respetar reglas de nombres de nodos sin espacios para render estable.
- La tabla debe mencionar explicitamente `src/rag/runtime` y `src/rag/evaluacion` post task-86.
- Si task-89 no esta hecha al ejecutar task-92, usar callout "pendiente" con link a task-89 en texto plano (IDs de tarea).
- Coordinar con task-91: evitar duplicacion extensa; task-92 es vista macro, task-91 es decision de servicio.
- Opcional: mencionar doc-005 como evidencia de auditoria.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Coherencia cruzada con task-86-90-89: si task-89 pendiente, parrafo condicional "pendiente rename qa".
- [ ] #2 Done sin archivar.
<!-- DOD:END -->
