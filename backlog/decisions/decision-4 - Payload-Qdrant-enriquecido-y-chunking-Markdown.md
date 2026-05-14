---
id: decision-4
title: Payload Qdrant enriquecido y chunking Markdown-aware en ingesta
date: '2026-05-14'
status: accepted
---

## Contexto

La ingesta (`scripts.indexar_corpus_qdrant`) usaba solo `SentenceSplitter`, lo que fragmentaba el Markdown sin respetar encabezados y dejaba un payload minimo en Qdrant. Eso limita filtros por tipo de pagina, especialidad o sede y complica listados deterministas (p. ej. directorio medico) en el agente M2.

## Decision

1. Exponer `CHUNK_STRATEGY` en `Configuracion` con valores `sentence` (retrocompatible) y `markdown` (estructural con `MarkdownNodeParser` de LlamaIndex y post-fractura por tamano).
2. Enriquecer el payload de cada punto con campos estructurados (`tipo_pagina`, `especialidad`, `sedes`, `headings_path`, `nombre_medico`, etc.) calculados por heuristicas puras en `src/rag/extractor_metadata.py`.
3. Crear indices de payload en Qdrant para `tipo_pagina`, `especialidad`, `sedes` y `seccion` al asegurar la coleccion (`asegurar_coleccion`).

## Consecuencias

### Positivas

- Mejor alineacion de chunks con secciones reales del sitio y metadata util para filtros en recuperacion (TASK-70).
- Heuristicas aisladas y cubiertas por pruebas unitarias.

### Negativas / riesgos

- Colecciones existentes sin reindexar no tendran los nuevos campos poblados en puntos antiguos; los filtros por payload requieren reingesta.
- El modo Qdrant `:memory:` no aplica indices de payload (advertencia del cliente); el comportamiento productivo depende del servidor Qdrant.

### Mitigacion

- Durante la migracion se recomienda una **coleccion nueva** (p. ej. `corpus_fvl_v2`) y A/B antes de apuntar el runtime.
- Mantener `CHUNK_STRATEGY=sentence` si se necesita reproducir exactamente la indexacion historica por tokens.

## Referencias

- Tarea: `backlog/tasks/task-69 - Chunking-semantico-Markdown-aware-y-payload-Qdrant-enriquecido.md`
- Stack M2: `backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md`
