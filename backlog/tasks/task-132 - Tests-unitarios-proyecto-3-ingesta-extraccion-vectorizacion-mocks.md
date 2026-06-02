---
id: TASK-132
title: Tests unitarios proyecto-3 ingesta extraccion vectorizacion mocks
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-24 17:02'
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
  - proyecto-3/tests/test_indexar_corpus_openfang.py
  - proyecto-3/tests/analisis_tsne/test_extraer_jsonl.py
  - proyecto-3/tests/analisis_tsne/test_vectorizar.py
  - proyecto-3/tests/hand/test_recordatorio_postop.py
  - proyecto-3/tests/guardrails/test_palabras_alarma.py
  - proyecto-3/tests/test_sincronizar_prompt_agente.py
  - proyecto-3/src/hand/recordatorio_postoperatorio.py
  - proyecto-3/pyproject.toml
  - proyecto-3/README.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Consolidar suite **pytest** sin red: chunking, idempotencia ingesta, parseo JSONL, vectorización stub, guardrails y Hand. Objetivo: `uv run pytest` verde en CI local.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `cd proyecto-3 && uv run pytest` — todos verdes sin `OPENAI_API_KEY` real
- [x] #2 Cobertura mínima: ingesta (fragmentar, front matter), extraer_jsonl, vectorizar (mock), guardrails, recordatorio sin sesiones
- [x] #3 **Negativo:** test demuestra que ingesta sin mock de OpenFang no llama red (monkeypatch)
- [x] #4 `uv run ruff check` limpio en `src/`, `ingesta/`, `analisis_tsne/`, `tests/`
- [x] #5 `pyproject.toml` configura `[tool.pytest.ini_options]` testpaths = `tests`
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
Inventario tests TASK-132:
- ingesta: tests/test_indexar_corpus_openfang.py (fragmentar, front matter, idempotencia, dry-run, mock embedder, test_dry_run_no_invoca_urlopen)
- extraccion: tests/analisis_tsne/test_extraer_jsonl.py
- vectorizacion: tests/analisis_tsne/test_vectorizar.py (cliente mock; test_main_sin_datos_no_llama_api)
- guardrails: tests/guardrails/test_palabras_alarma.py
- recordatorio: tests/hand/test_recordatorio_postop.py (sin sesiones)

AC #3: dry-run y tests con mock no deben invocar urllib.request.urlopen ni embedder real OpenAI.

```bash
cd proyecto-3 && uv run pytest -q && uv run ruff check src ingesta analisis_tsne tests
```

Ruff: exclude analisis_tsne/notebooks en pyproject.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Suite pytest proyecto-3 consolidada: 133 tests sin OPENAI_API_KEY real. Cobertura ingesta (test_indexar_corpus_openfang.py + test_dry_run_no_invoca_urlopen AC#3), extraer_jsonl, vectorizar mock, guardrails y recordatorio sin sesiones. Ruff limpio (exclude notebooks; fix imports recordatorio y F401 en test_sincronizar). pyproject pytest.ini_options y README con comandos de verificacion.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Suite estable
- [x] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
