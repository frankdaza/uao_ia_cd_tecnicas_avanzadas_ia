---
id: TASK-89
title: Renombrar src/qa/ a src/laboratorio/qa_legacy/ y actualizar imports
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-16 16:50'
updated_date: '2026-05-16 17:14'
labels:
  - migracion
  - clean-architecture
  - modulo-2
  - qa-legacy
  - refactor
dependencies:
  - TASK-85
  - TASK-86
  - TASK-88
references:
  - src/qa/
  - src/laboratorio/qa_legacy/
  - tests/qa/
  - README.md
  - src/qa/__init__.py (shim deprecado)
documentation:
  - >-
    backlog/decisions/decision-6 -
    Migracion-Incremental-Clean-Architecture-M2.md
  - backlog/docs/doc-004 - Estudio-Migracion-Clean-Architecture.md
  - backlog/docs/doc-005 - Auditoria-Imports-Migracion-Clean-Architecture.md
priority: medium
ordinal: 0.48828125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Sub-decision 3 de decision-6 (rename diferido): mover `src/qa/` a `src/laboratorio/qa_legacy/` y actualizar imports.

## Objetivo

Reducir confusion auditora entre Modulo 1/laboratorio y runtime M2, despues de estabilizar imports de rag (task-86) y documentar el rol (task-88).

## Shim opcional

`src/qa/__init__.py` puede emitir DeprecationWarning y reexportar simbolos minimos durante una ventana corta; documentar fecha de retiro del shim en README o en esta tarea.

## Fuera de alcance

Eliminar el paquete sin reemplazo (decision-6 lo prohibe sin tarea dedicada y suite verde).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El codigo fuente de qa_legacy vive bajo src/laboratorio/qa_legacy/ con __init__.py y modulos migrados.
- [x] #2 tests/qa y scripts que importaban src.qa actualizan imports al nuevo paquete.
- [x] #3 Opcional documentado: shim src/qa/__init__.py con DeprecationWarning y reexport limitado durante periodo de gracia (si el equipo lo elige).
- [x] #4 `rg "from src\\.qa\\."` solo encuentra el shim (si existe) o cero resultados.
- [x] #5 README.md actualizado: ruta nueva y rol de laboratorio; coherente con task-88.
- [x] #6 `uv run pytest tests/qa` (y suite relacionada) verde.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Basarse en doc-005 para lista de imports `src.qa`.
2. git mv de modulos a `src/laboratorio/qa_legacy/`; ajustar namespaces.
3. Actualizar tests/qa, scripts, notebooks.
4. (Opcional) Implementar shim deprecado en `src/qa/__init__.py` con plan de retiro.
5. Actualizar README: nueva ruta y significado de laboratorio.
6. `uv run pytest tests/qa` + smoke import del paquete nuevo.
7. Cerrar tarea.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Crear `src/laboratorio/__init__.py` y `src/laboratorio/qa_legacy/__init__.py` si faltan.
- Preferir una sola ventana de churn: coordinar merge despues de task-86.
- Si se usa shim, listar simbolos publicos minimos (`__all__`) para evitar reexport amplio.
- Actualizar cualquier referencia en `pyproject` o mypy paths si existiera (poco probable).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se movio el paquete con git mv a src/laboratorio/qa_legacy/ (nuevo src/laboratorio/__init__.py). Imports internos y tests (tests/qa, parches en test_cliente_openai, import dinamico en test_router_grafo) apuntan a src.laboratorio.qa_legacy. Shim deprecado en src/qa/__init__.py con DeprecationWarning y retiro previsto 2026-08-01 (no contiene "from src.qa."). README, AGENTS.md, CLAUDE.md, project-structure.mdc y skills llm-backend/qa-prompt-engineering alineados. Comentarios en meta_prompt y docstring en prompt_institucional actualizados. uv run pytest: 376 passed, 9 skipped.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Done sin task_complete.
- [x] #2 CHANGELOG o nota en PR si el equipo lo exige; si no, README basta.
<!-- DOD:END -->
