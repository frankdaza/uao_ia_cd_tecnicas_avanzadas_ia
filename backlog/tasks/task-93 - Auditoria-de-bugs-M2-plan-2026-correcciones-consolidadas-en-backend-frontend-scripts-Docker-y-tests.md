---
id: TASK-93
title: >-
  Auditoria de bugs M2 (plan 2026): correcciones consolidadas en backend,
  frontend, scripts, Docker y tests
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-16 12:55'
updated_date: '2026-05-16 17:54'
labels:
  - modulo-2
  - bugs
  - sse
  - docker
  - tests
dependencies: []
references:
  - tests/stream_mock_agente_m2.py
  - tests/agentes/test_router_grafo.py
  - scripts/limpiar_corpus_markdown.py
  - scripts/agrupar_corpus_markdown.py
  - frontend/src/lib/api.ts
documentation:
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
  - RESUMEN.md
priority: high
ordinal: 0.030517578125
---

## Contexto

Implementacion del plan de auditoria M2 (A1–A7, B1–B13, C1–C12): SSE y chat,
pool Postgres en stream, listados sin filtro, grafo async, historial/admin,
RAG razon mmr, docs Docker, fixture de stream minimo, etc.

## Definition of Done

- `uv run pytest`: suite verde (387 passed, skips marcados).
- `pnpm --dir frontend test`: Vitest verde.
- Sin editar el archivo `.cursor/plans/auditoria_de_bugs_m2_*.plan.md`.

## finalSummary

Correcciones aplicadas en el arbol principal; mock `astream_events` minimo en
`tests/stream_mock_agente_m2.py`; tests del router usan `ainvoke`;
`_relativo_seguro` devuelve `Path`; export duplicado corregido en `api.ts`.
