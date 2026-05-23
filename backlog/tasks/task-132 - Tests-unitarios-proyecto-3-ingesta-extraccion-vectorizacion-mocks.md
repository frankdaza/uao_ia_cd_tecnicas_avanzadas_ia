---
id: TASK-132
title: 'Tests unitarios proyecto-3 ingesta extraccion vectorizacion mocks'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - tests
milestone: m-1
dependencies:
  - TASK-121
  - TASK-128
  - TASK-129
references:
  - proyecto-3/tests/
  - proyecto-3/pyproject.toml
modified_files:
  - proyecto-3/tests/ingesta/test_indexar_corpus.py
  - proyecto-3/tests/analisis_tsne/test_extraer_jsonl.py
  - proyecto-3/tests/analisis_tsne/test_vectorizar.py
  - proyecto-3/tests/hand/test_recordatorio_postop.py
  - proyecto-3/tests/guardrails/test_palabras_alarma.py
  - proyecto-3/pyproject.toml
priority: high
ordinal: 1320
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Consolidar suite **pytest** sin red: chunking, idempotencia ingesta, parseo JSONL, vectorización stub, guardrails y Hand. Objetivo: `uv run pytest` verde en CI local.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `cd proyecto-3 && uv run pytest` — todos verdes sin `OPENAI_API_KEY` real
- [ ] #2 Cobertura mínima: ingesta (fragmentar, front matter), extraer_jsonl, vectorizar (mock), guardrails, recordatorio sin sesiones
- [ ] #3 **Negativo:** test demuestra que ingesta sin mock de OpenFang no llama red (monkeypatch)
- [ ] #4 `uv run ruff check` limpio en `src/`, `ingesta/`, `analisis_tsne/`, `tests/`
- [ ] #5 `pyproject.toml` configura `[tool.pytest.ini_options]` testpaths = `tests`
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Estructura `tests/` por dominio.
2. Fixtures Markdown/PDF mínimos en `tests/fixtures/`.
3. Configurar pytest y ruff en pyproject.
4. Integrar en README comando de verificación.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```toml
# pyproject.toml fragmento
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "ingesta", "analisis_tsne/src"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

```bash
cd proyecto-3 && uv run pytest -q && uv run ruff check .
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Suite estable
- [ ] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
