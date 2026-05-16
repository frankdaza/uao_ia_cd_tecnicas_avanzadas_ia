---
id: TASK-86
title: Reorganizar src/rag/ en runtime/ y evaluacion/ (decision-6)
status: In Progress
assignee:
  - Frank Daza
created_date: '2026-05-16 16:50'
updated_date: '2026-05-16 16:55'
labels:
  - migracion
  - clean-architecture
  - modulo-2
  - rag
  - refactor
dependencies:
  - TASK-85
references:
  - src/rag/
  - src/agentes/
  - src/api/
  - scripts/indexar_corpus_qdrant.py
  - tests/rag/
documentation:
  - >-
    backlog/decisions/decision-6 -
    Migracion-Incremental-Clean-Architecture-M2.md
  - backlog/docs/doc-004 - Estudio-Migracion-Clean-Architecture.md
  - backlog/docs/doc-005 - Auditoria-Imports-Migracion-Clean-Architecture.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Sub-decision 2 de decision-6: subdividir `src/rag/` en `runtime/` (consultas en cada peticion del agente) y `evaluacion/` (metricas, laboratorio).

## Objetivo

Mover los archivos indicados en el ADR, actualizar imports en consumidores (`src/agentes/`, `src/api/`, `scripts/`, `tests/`) y mantener la suite verde.

## Archivos runtime (lista ADR)

qdrant_store.py, embeddings.py, recuperador_denso.py, recuperador_listados.py, intencion.py, diversificador_mmr.py, reranker_cross_encoder.py, filtros_listado_heuristica.py, extractor_metadata.py.

## Archivos evaluacion

metricas_eval.py (+ utilidades compartidas si doc-005 lo exige).

## Estrategia

Preferir actualizar imports explicitos; reexport en `src/rag/__init__.py` solo como compatibilidad temporal documentada.

## Invariantes

No cambiar stack decision-3; no BM25 en runtime; contratos Qdrant decision-4 intactos.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Existe src/rag/runtime/ con los modulos listados en decision-6 y __init__.py si aplica.
- [ ] #2 Existe src/rag/evaluacion/ con metricas_eval.py (y utilidades de evaluacion si task-85 las identifico).
- [ ] #3 Todos los imports del proyecto apuntan a las nuevas rutas o a reexports explicitos documentados en src/rag/__init__.py.
- [ ] #4 `uv run pytest tests/rag tests/agentes tests/api` pasa (ajustar subset si CI documenta otro alcance, pero justificar en notas).
- [ ] #5 Smoke: `uv run python -c "from src.rag.runtime import qdrant_store"` (o modulo equivalente) sin error.
- [ ] #6 El script scripts/indexar_corpus_qdrant.py importa correctamente tras el cambio (smoke import o ejecucion dry-run si existe flag).
- [ ] #7 Diff acotado a movimiento de archivos + actualizacion de imports; sin cambios funcionales de negocio no justificados.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Consumir doc-005: lista cerrada de archivos y consumidores a tocar.
2. Crear carpetas `src/rag/runtime/` y `src/rag/evaluacion/` con `__init__.py` vacios o con reexports minimos.
3. Mover archivos con git mv segun lista ADR; ajustar imports internos entre modulos rag.
4. Actualizar imports en `src/agentes/`, `src/api/`, `scripts/`, `tests/` (y cualquier otro listado en doc-005).
5. Ejecutar smoke imports y `uv run pytest tests/rag tests/agentes tests/api`.
6. Verificar `scripts/indexar_corpus_qdrant.py` (import o dry-run).
7. PR pequeno: solo estructura + imports; descripcion enlaza decision-6.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Usar `git mv` cuando sea posible para preservar historial.
- Evitar import circular: `evaluacion` no debe importar modulos de `runtime` en tiempo de import del paquete salvo patron ya existente; si metricas_eval importa runtime, documentar el grafo de dependencias en comentario breve.
- Revisar `pyproject.toml` / paquetes si hubiera entry points que referencien rutas viejas (poco probable).
- Tras mover, ejecutar ruff/format si el proyecto lo usa en pre-commit.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Al cierre: status Done sin archivar automaticamente.
- [ ] #2 Convenciones de codigo del repo respetadas (ASCII en identificadores Python).
<!-- DOD:END -->
