---
id: decision-1
title: MVP usa BM25 a nivel archivo (sin chunking ni embeddings)
date: '2026-04-26'
status: accepted
---

## Contexto

Fase 1 del proyecto. El cliente exige una solución sencilla, sin vector DB, que sirva como base para iteraciones posteriores con embeddings.

## Decisión

La recuperación se hace con `rank-bm25` evaluando archivos Markdown completos. El archivo recuperado se inyecta íntegro como contexto al prompt del LLM.

## Consecuencias

### Positivas

- Setup mínimo, fácil de explicar y demostrar.
- Trazabilidad total: 1 pregunta → 1 archivo identificable.

### Negativas / riesgos

- Páginas largas pueden exceder `num_ctx` del LLM.
- Vocabulario repetido entre secciones puede llevar a falsos positivos.

## Alternativas consideradas

- Chunking + embeddings + Chroma (descartado para fase 1; planeado para módulo 2).
