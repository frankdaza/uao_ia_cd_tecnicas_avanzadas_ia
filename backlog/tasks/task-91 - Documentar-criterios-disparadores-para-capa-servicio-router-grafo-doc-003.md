---
id: TASK-91
title: Documentar criterios disparadores para capa servicio router-grafo (doc-003)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-16 16:50'
updated_date: '2026-05-16 17:26'
labels:
  - migracion
  - clean-architecture
  - modulo-2
  - documentacion
  - api
dependencies:
  - TASK-85
references:
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
  - src/api/routers/agente.py
documentation:
  - >-
    backlog/decisions/decision-6 -
    Migracion-Incremental-Clean-Architecture-M2.md
  - backlog/docs/doc-004 - Estudio-Migracion-Clean-Architecture.md
priority: low
ordinal: 0.1220703125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Sub-decision 6 de decision-6: capa de servicio delgada solo si `src/api/routers/agente.py` acumula logica de negocio; mientras tanto el router puede llamar a la factoria del grafo directamente.

## Objetivo

Documentar criterios objetivos (sintomas) y anti-patrones para decidir la extraccion futura de un modulo tipo `src/aplicacion/agente_servicio.py` sin implementarlo aun.

## Alcance

Solo edicion de `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md`.

## Referencia normativa

Seccion "Criterio de cierre (regla de stop)" en decision-6.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 En doc-003 existe seccion dedicada (encabezado explicito) sobre cuando introducir capa de servicio delgada entre FastAPI y la factoria del grafo.
- [x] #2 La seccion lista al menos 4 sintomas disparadores concretos (ej. acumulacion de logica en router, multiples consumidores HTTP/CLI, validaciones complejas, duplicacion de mapping DTO).
- [x] #3 Se cita textualmente o parafrasea el criterio de stop de decision-6 (no crear aplicacion/ generica sin segundo consumidor).
- [x] #4 Se enlaza decision-6 y doc-004.
- [x] #5 No hay cambios en archivos .py del backend (solo Markdown en backlog/docs).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer doc-003 completo y ubicar mejor ancla (arquitectura o despliegue).
2. Redactar seccion "Capa de servicio router -> grafo (condicional)" con sintomas, anti-patrones y regla de stop citando decision-6.
3. Anadir enlaces relativos a decision-6 y doc-004.
4. Actualizar `updated_date` en front matter de doc-003.
5. Revisar enlaces internos del documento.
6. Cerrar tarea (Done sin archivar).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Mantener consistencia con decision-2 (SSE) y decision-3 (stack): la capa servicio no debe duplicar contratos HTTP.
- Incluir contraejemplo: crear `src/aplicacion/` con muchos archivos vacios viola el criterio de stop.
- Revisar encabezados existentes de doc-003 para no duplicar secciones; integrar o anexar subseccion clara.
- task-91 puede ejecutarse en paralelo a codigo pero conviene leer doc-003 actual antes de editar.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se anadio la seccion 8 en doc-003 (Capa de servicio router a grafo, condicional) con cuatro sintomas disparadores, anti-patrones, cita de la regla de stop de decision-6 y enlaces a decision-6 y doc-004. Se actualizo updated_date del documento y la lista de referencias internas.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Actualizar updated_date en front matter de doc-003 si la regla backlog-docs lo requiere.
- [x] #2 Revision de enlaces relativos rotos.
<!-- DOD:END -->
