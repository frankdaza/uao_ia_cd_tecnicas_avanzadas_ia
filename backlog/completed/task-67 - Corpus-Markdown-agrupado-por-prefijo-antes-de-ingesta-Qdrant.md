---
id: TASK-67
title: >-
  Corpus Markdown agrupado por prefijo/categoría (paso intermedio) antes de
  ingesta Qdrant y evaluación de recuperación RAG
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-14 00:00'
updated_date: '2026-05-14 19:32'
labels:
  - rag
  - qdrant
  - corpus
  - scripts
  - modulo-2
dependencies:
  - TASK-53
  - TASK-54
references:
  - scripts/indexar_corpus_qdrant.py
  - scripts/agrupar_corpus_markdown.py
  - config/agrupacion_corpus_valledellili.yaml
  - data/markdown/valledellili-org/
  - src/rag/recuperador_denso.py
documentation:
  - .claude/skills/text-chunking/SKILL.md
priority: medium
ordinal: 250
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

### Problema

La recuperación RAG en Qdrant a menudo devuelve vacío. Hipótesis: el corpus está muy fragmentado (una página por archivo) y el contenido útil queda repartido en muchos chunks con similitud baja frente a la consulta.

### Objetivo

Implementar un script de preprocesamiento que agrupe archivos `.md` bajo reglas de **prefijo/patrón** (por ejemplo `buscador-integral-q-*.md`, `directorio-medico-*.md`) en **nuevos** Markdown con front matter válido para [`scripts/indexar_corpus_qdrant.py`](scripts/indexar_corpus_qdrant.py), preservando trazabilidad en el cuerpo (secciones por documento fuente con URL).

### Alcance

- **Salida derivada** bajo `data/processed/markdown_agrupado/valledellili-org/` por defecto; **no** sobrescribir el corpus canónico en `data/markdown/`.
- Reglas versionadas en [`config/agrupacion_corpus_valledellili.yaml`](config/agrupacion_corpus_valledellili.yaml) y manifiesto JSON de auditoría.
- Documentar migración en Qdrant: reindex con `--markdown-dir` apuntando al derivado; evitar duplicados semánticos en la misma colección (colección temporal para A/B o purga del prefijo antiguo cuando aplique).

### Evaluación A/B

Checklist y script opcional de consultas de ejemplo (ver [`scripts/README.md`](scripts/README.md) y [`config/evaluacion_rag_consultas_ejemplo.json`](config/evaluacion_rag_consultas_ejemplo.json)).

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Script ejecutable con `uv run python -m scripts.agrupar_corpus_markdown` y `--help` claro
- [x] #2 Entrada por defecto `data/markdown/valledellili-org/`; salida configurable (defecto `data/processed/markdown_agrupado/valledellili-org/`)
- [x] #3 Cada archivo generado cumple front matter `---` parseable por el ingesta actual
- [x] #4 Trazabilidad: en el cuerpo, cada bloque indica archivo origen y `source_url` de la página fuente cuando exista en el front matter original
- [x] #5 Reglas externalizadas en YAML; al menos dos familias de ejemplo (`buscador-integral-q-*`, `directorio-medico-*`)
- [x] #6 Documentación en `scripts/README.md`: agrupación + indexación con `--markdown-dir` y notas de `--purgar` / `--collection`
- [x] #7 Mini evaluación: JSON de consultas de ejemplo + script opcional (`eval_recuperacion_consultas.py`) con modo validación sin Qdrant

<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->

1. Inventariar prefijos en `valledellili-org` (manual o script auxiliar) y validar patrones sin colisiones de `archivo_salida`.
2. Definir esquema YAML de grupos (`patron_nombre`, `archivo_salida`, `titulo`, `seccion`, `source_url_canonica` opcional).
3. Implementar `scripts/agrupar_corpus_markdown.py`: asignación por orden de grupos, orden lexicográfico de rutas, fusión de cuerpos con secciones `##`.
4. Escribir `tests/scripts/test_agrupar_corpus_markdown.py` (orden estable, YAML válido, copia de no agrupados, `--solo-grupos`).
5. Smoke local: agrupación → `indexar_corpus_qdrant --limit` sobre salida.
6. Documentar estrategia Qdrant (colección temporal vs purga de prefijo).

<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

- Los hubs tipo `buscador-integral-q-*` pueden aportar poco a la semántica; la config permite desactivar grupos comentando entradas.
- Si un archivo consolidado supera tamaño práctico para embedder, valorar troceo en partes (`directorio-medico-parte-01.md`) en una iteración futura.
- La purga de Qdrant (`--purgar`) opera por prefijo del directorio de corpus; cambiar de `data/markdown/...` a `data/processed/markdown_agrupado/...` **no** elimina vectores antiguos: usar colección de prueba o purga manual del prefijo previo.

<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->

- [x] #1 Criterios de aceptación verificados en código y documentación
- [x] #2 `uv run pytest tests/scripts/test_agrupar_corpus_markdown.py` pasa
- [x] #3 Sin secretos en YAML de agrupación ni en la tarea
- [x] #4 Tras validación en entorno real, pasar `status` a **Done** (sin archivar; ver regla `backlog-workflow.mdc`)

<!-- DOD:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->

Implementacion inicial: `scripts/agrupar_corpus_markdown.py`, `config/agrupacion_corpus_valledellili.yaml`, salida bajo `data/processed/markdown_agrupado/`, manifiesto `_manifest_agrupacion.json`, pruebas en `tests/scripts/test_agrupar_corpus_markdown.py`, documentacion en `scripts/README.md`, evaluacion ligera con `config/evaluacion_rag_consultas_ejemplo.json` y `scripts/eval_recuperacion_consultas.py` (modo `--solo-validar-json` sin Qdrant).

Cierre: `uv run pytest tests/scripts/test_agrupar_corpus_markdown.py` OK; `uv run python -m scripts.eval_recuperacion_consultas --solo-validar-json` OK; smoke sobre corpus real con `agrupar_corpus_markdown --limpiar-salida --solo-grupos` (987 archivos leidos, 632 en grupos, 2 salidas agrupadas) e `indexar_corpus_qdrant` sobre `data/processed/markdown_agrupado/valledellili-org` con `QDRANT_URL=:memory:`, `EMBEDDING_PROVIDER=huggingface`, `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`, `EMBEDDING_DIMS=384` (2 archivos, 2743 chunks indexados).

<!-- SECTION:FINAL_SUMMARY:END -->
