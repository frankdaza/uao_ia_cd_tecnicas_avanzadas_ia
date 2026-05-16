---
id: TASK-92
title: >-
  Cierre documental: nucleo vs laboratorio, diagrama doc-003 y README
  post-migracion
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-16 16:50'
updated_date: '2026-05-16 17:30'
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
ordinal: 0.06103515625
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
- [x] #1 doc-003 incluye diagrama Mermaid de limites alineado a decision-6 (Presentacion HTTP, Orquestacion agente, infra rag runtime/evaluacion, laboratorio).
- [x] #2 doc-003 incluye tabla canonica modulo -> categoria (nucleo M2 / laboratorio / scripts / infra OLTP).
- [x] #3 README.md refleja arbol conceptual post-migracion: rag/runtime, rag/evaluacion; ausencia de src/app; nota sobre qa segun estado (src/qa vs laboratorio/qa_legacy si task-89 ya cerro).
- [x] #4 Front matter de doc-003 tiene updated_date coherente con el cambio sustancial.
- [x] #5 `uv run pytest` no es obligatorio en tarea solo-doc; si se toca README sin codigo, indicar N/A en notas de cierre.
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
- Cierre: **`uv run pytest` N/A** (cambios solo en documentacion; sin modificacion de codigo Python productivo). Se elimino resto local no versionado bajo `src/app/__pycache__` para alinear el arbol de trabajo con TASK-87.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se documento en doc-003 la seccion 1.1 (Mermaid decision-6, tabla modulo-categoria, rutas runtime/evaluacion). README actualizado (nucleo vs laboratorio, estructura, src/app, TASK-89). Pytest N/A (solo docs). Tarea Done sin archivar.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Coherencia cruzada con task-86-90-89: si task-89 pendiente, parrafo condicional "pendiente rename qa".
- [x] #2 Done sin archivar.
<!-- DOD:END -->
