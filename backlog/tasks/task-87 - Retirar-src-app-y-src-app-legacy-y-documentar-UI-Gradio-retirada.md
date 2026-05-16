---
id: TASK-87
title: Retirar src/app/ y src/app/legacy/ y documentar UI Gradio retirada
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-16 16:50'
updated_date: '2026-05-16 16:50'
labels:
  - migracion
  - clean-architecture
  - modulo-2
  - cleanup
  - legacy
dependencies:
  - TASK-85
references:
  - src/app/
  - src/app/legacy/
  - README.md
documentation:
  - >-
    backlog/decisions/decision-6 -
    Migracion-Incremental-Clean-Architecture-M2.md
  - backlog/docs/doc-004 - Estudio-Migracion-Clean-Architecture.md
  - backlog/docs/doc-002 - Migracion-Frontend-React-Vite-Backend-FastAPI.md
priority: medium
ordinal: 87000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Sub-decision 4 de decision-6: retirar `src/app/` y `src/app/legacy/` (paquetes vacios salvo `__init__.py`) y documentar la UI Gradio retirada.

## Objetivo

Confirmar ausencia de imports, eliminar carpetas y anadir nota en README raiz apuntando a doc-002 e historial git.

## Precaucion

No borrar historial en git; solo el arbol de trabajo actual.

## Fuera de alcance

Reintroducir Gradio o rutas legacy en FastAPI.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Las carpetas src/app/ y src/app/legacy/ ya no existen en el arbol del repo.
- [ ] #2 `rg "from src\\.app|import src\\.app"` no devuelve referencias en codigo fuente activo (salvo historial git).
- [ ] #3 README.md en la raiz incluye nota visible: UI Gradio retirada; historial en git y en backlog/docs/doc-002.
- [ ] #4 `uv run pytest` pasa en el alcance acordado con doc-005 (idealmente suite completa).
- [ ] #5 La eliminacion esta respaldada por la auditoria task-85 (sin imports ocultos).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Verificar doc-005 / rg: cero consumidores de src.app.
2. Eliminar carpetas `src/app/` y `src/app/legacy/` (git rm -r).
3. Editar README.md: parrafo corto + enlace a doc-002.
4. `uv run pytest` y corregir solo roturas directamente causadas por la eliminacion.
5. Marcar AC y cerrar tarea (Done sin archivar).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Antes de `git rm -r`, ejecutar los mismos rg que task-85 y pegar evidencia en el PR o en comentario de commit.
- Si algun test importaba `src.app` por error, corregir en la misma PR (fuera de alcance ideal pero necesario para verde).
- Mantener tono institucional neutro en README.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Cierre con status Done sin task_complete.
- [ ] #2 Sin eliminar documentacion util de doc-002; solo referenciarla.
<!-- DOD:END -->
