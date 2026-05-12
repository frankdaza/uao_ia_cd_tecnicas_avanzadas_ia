---
id: decision-1
title: MVP usa BM25 a nivel archivo (sin chunking ni embeddings)
date: '2026-04-26'
status: superseded
---

> **Alcance de la sustitución:** La elección de BM25 a nivel archivo sigue siendo el **registro histórico del MVP de la Fase 1** y del código legacy asociado. En cambio, el **camino de recuperación en el runtime productivo del Módulo 2** (solo similitud densa en Qdrant, sin BM25 ni RAG híbrido) queda definido en [decision-3 — Arquitectura agente M2](decision-3%20-%20Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md).

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
