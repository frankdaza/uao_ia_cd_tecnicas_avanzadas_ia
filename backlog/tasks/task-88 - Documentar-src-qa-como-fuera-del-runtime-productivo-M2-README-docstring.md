---
id: TASK-88
title: Documentar src/qa/ como fuera del runtime productivo M2 (README + docstring)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-16 16:50'
updated_date: '2026-05-16 16:50'
labels:
  - migracion
  - clean-architecture
  - modulo-2
  - documentacion
  - qa-legacy
dependencies:
  - TASK-85
references:
  - README.md
  - src/qa/__init__.py
  - src/qa/
documentation:
  - >-
    backlog/decisions/decision-6 -
    Migracion-Incremental-Clean-Architecture-M2.md
  - backlog/docs/doc-004 - Estudio-Migracion-Clean-Architecture.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: medium
ordinal: 88000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Sub-decision 3 de decision-6 (camino conservador): aclarar que `src/qa/` no forma parte del runtime M2 en produccion.

## Objetivo

Documentar en README raiz y en docstring del paquete `src/qa` el rol de laboratorio / Modulo 1 y tests, sin renombrar todavia el arbol.

## Fuera de alcance

Mover o renombrar `src/qa/` (eso es task-89).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 README.md incluye seccion explicita "Nucleo productivo M2 vs laboratorio" (o titulo equivalente) que aclara que src/qa no participa en POST /api/agente/stream.
- [ ] #2 src/qa/__init__.py contiene docstring de paquete que describe rol M1/pruebas y apunta a src/agentes para el agente M2.
- [ ] #3 No se modifica la logica de negocio dentro de src/qa/*.py (solo docstring de paquete si hace falta).
- [ ] #4 Enlaces en README a doc-003 y decision-3 para el camino productivo.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Redactar seccion en README: nucleo (api, agentes, persistencia, rag runtime) vs laboratorio (qa, scripts, evaluacion rag).
2. Anadir docstring de paquete en `src/qa/__init__.py`.
3. Enlazar doc-003 y decision-3 desde README.
4. Relectura rapida de consistencia con doc-004.
5. Cerrar tarea con pytest si hubo cambios accidentales (no deberia).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Alinear wording con decision-6: "no forma parte del runtime M2 en produccion".
- Evitar duplicar doc-003 completo en README; solo remision y tabla breve.
- El docstring en `src/qa/__init__.py` debe ser import-safe (sin efectos secundarios).
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Status Done sin archivar.
- [ ] #2 Revision ortografica en espanol latinoamericano.
<!-- DOD:END -->
