---
id: TASK-20
title: Endurecer recuperador BM25 con higiene del corpus lexical de tamano medio
status: Done
assignee: []
created_date: '2026-04-29'
updated_date: '2026-04-29 05:50'
labels:
  - retrieval
  - qa
dependencies:
  - TASK-8
  - TASK-18
references:
  - src/retrieval/recuperador.py
  - src/retrieval/sinonimos.py
  - src/retrieval/_stopwords_nltk_es.py
  - src/qa/pipeline.py
  - tests/retrieval/test_recuperador_bm25.py
ordinal: 0.0019073486328125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Mejorar calidad de recuperacion BM25 cuando el corpus crece (p. ej. muchos perfiles con boilerplate compartido), sin RAG vectorial ni segmentacion granular estilo chunk externo:

- Omitir SERPs tipo `buscador-integral-q-*`.
- Dedupe `slug-N.md` frente `slug.md` usando `fecha_extraccion` / longitud.
- Quitar bloque navegacion comun antes de BM25 mediante patron Facebook → `### Servicios para ti`.
- BM25F lexical por repetir titulo y seccion.
- Snowball ES + lista stopwords español NLTK embebida.
- Sinonimos opcionales en la pregunta (`expandir_query`).
- Top-K 5 pipeline y umbral relativo BM25 contra el mejor puntaje (~0.3).

## Criterios de aceptacion

- [x] `cargar_corpus` aplica filtros SERP/dedupe y tokeniza igual que query.
- [x] `PipelineQa` usa `K_TOP_DOCUMENTOS = 5`.
- [x] Pruebas unitarias actualizadas o nuevas en `tests/retrieval/`.
- [x] `uv run pytest` verde.
<!-- SECTION:DESCRIPTION:END -->

## Definition of Done

- Implementacion alineada al plan aprobado; tests verdes; no se archiva la tarea (permanece en `backlog/tasks/`).

## finalSummary

Se implemento higiene al cargar (SERP, dedupe `slug-N`, limpieza boilerplate Valledellili), BM25 campo ponderado repetido (`texto_indexable_bm25`), Snowball + stopwords NLTK snapshot (`_stopwords_nltk_es.py`), expansion de interrogativos antes del stem efectivo (`_TERMINOS_RELACIONADOS_CON_INTERROGATIVOS` + `_RAIZ_DESCARTE_POS_STEM`), `expandir_query` (`sinonimos.py`), umbral relativo contra max score en `buscar_top`, `K_TOP_DOCUMENTOS=5` en pipeline.
