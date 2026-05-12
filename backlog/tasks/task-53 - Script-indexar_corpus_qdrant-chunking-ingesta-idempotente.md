---
id: TASK-53
title: Script scripts/indexar_corpus_qdrant.py (chunking LlamaIndex + ingesta idempotente a Qdrant)
status: To Do
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-11 00:00'
labels:
  - rag
  - qdrant
  - scripts
  - modulo-2
dependencies:
  - TASK-52
references:
  - scripts/indexar_corpus_qdrant.py
  - data/markdown/
  - src/rag/qdrant_store.py
  - src/rag/embeddings.py
documentation:
  - .claude/skills/text-chunking/SKILL.md
priority: high
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El corpus canónico vive en **`data/markdown/`** (p. ej. `valledellili-org/**/*.md`). Tras el M2, **el runtime del agente no lee markdown**; solo el script de ingesta transforma esos archivos en chunks vectoriales en **Qdrant**.

## Objetivo

Implementar `scripts/indexar_corpus_qdrant.py` como CLI que:

1. Recorre `data/markdown/valledellili-org/**/*.md` (parametrizable por flag `--glob` o ruta base).
2. Parsea **front matter YAML** con `pyyaml` usando un parser mínimo propio (delimitadores `---`); **prohibido** importar `src/retrieval/recuperador.py`.
3. Aplica `SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)` de LlamaIndex.
4. Calcula `id_chunk = sha256(f"{ruta}:{chunk_index}:{texto}".encode()).hexdigest()` (o esquema equivalente documentado) para **upsert idempotente**.
5. Sube vectores y payload a Qdrant con metadatos: `{ archivo, titulo, source_url, seccion, chunk_index, content_hash }`.

## Flags CLI

- `--purgar`: borra puntos de la colección que ya no existen en el corpus (definir estrategia segura).
- `--limit`: máximo de archivos o chunks para pruebas rápidas.
- `--collection`: override del nombre de colección.

## Salida

Imprime estadísticas: número de documentos markdown, número de chunks, dimensiones, tiempos.

## Smoke de idempotencia

Segunda ejecución sin cambios en corpus → **0 chunks insertados** (o solo updates sin cambio detectado), documentado en tests o log esperado.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 Script ejecutable con `uv run python scripts/indexar_corpus_qdrant.py`
- [ ] #2 No importa módulos BM25 legacy
- [ ] #3 Ingesta idempotente verificada por test o log de conteos
- [ ] #4 Payload contiene los metadatos mínimos listados
- [ ] #5 Flags `--purgar`, `--limit`, `--collection` implementados y documentados en `--help`
- [ ] #6 Manejo de archivos sin front matter o YAML inválido con warning y skip
- [ ] #7 Estadísticas finales legibles en stdout
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Reutilizar factories de task-52 para embeddings y vector store.
2. Implementar pipeline lectura → nodos LlamaIndex → embeddings batch.
3. Upsert por `id_chunk` con batching configurable.
4. Añadir prueba unitaria/integration con Qdrant `:memory:` o contenedor.
5. Documentar requisito de `OPENAI_API_KEY` para embeddings OpenAI.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Para corpus grande, soportar `--batch-size` y backoff ante rate limits de OpenAI.
- `content_hash` puede ser sha256 del texto del chunk para deduplicación.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 `uv run pytest` incluye test de idempotencia o script verificable en CI
- [ ] #2 `ruff check` en el script si aplica (módulo bajo `scripts/` puede tener exclusiones documentadas)
- [ ] #3 README o doc-003 enlazará comandos (task-62/63)
<!-- DOD:END -->
