---
id: TASK-101
title: >-
  Ingesta PDF a vector store LangChain (RecursiveCharacterTextSplitter, Qdrant
  TAAM)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
labels:
  - modulo-3
  - taam
  - rag
  - langchain
milestone: m-0
dependencies:
  - TASK-100
documentation:
  - >-
    backlog/docs/actividades/Actividad del Módulo 3_ Productización, Despliegue
    Avanzado y Sistemas Agénticos.md
priority: high
ordinal: 2050
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La rúbrica M3 exige chunking con **RecursiveCharacterTextSplitter** y vector stores **nativos LangChain** (no solo LlamaIndex de M2). La ingesta debe ser **idempotente** por `tipo_procedimiento_id` + hash PDF.

## Objetivo

Script `proyecto-2/scripts/ingestar_protocolo_pdf.py` y servicio invocable desde API admin tras upload.

## Diseño

1. Extraer texto PDF (`pdfplumber` o pypdf — documentar elección).
2. `RecursiveCharacterTextSplitter` con tamaños acordados en ADR (p. ej. chunk 800, overlap 120).
3. Embeddings vía LangChain (`OpenAIEmbeddings` o equivalente del curso).
4. Colección Qdrant dedicada: `taam_protocolos` con payload: `tipo_procedimiento_id`, `pagina`, `nombre_archivo`, `version`.
5. Ante re-ingesta: borrar puntos con mismo `tipo_procedimiento_id` + `version` anterior, luego upsert.
6. Reintentos con backoff en upsert (patrón task-80 M2).

## Integración

- Tras `POST /api/admin/procedimientos`, encolar o invocar ingesta síncrona con timeout razonable; estado `indexacion_estado` en tabla.

## Fallas a evitar

- Mezclar colección M2 `corpus_*` con TAAM.
- Indexar PDF vacío o escaneado sin OCR (documentar limitación en UC).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Script uv run ingesta un PDF de prueba y reporta conteo de chunks
- [ ] #2 Puntos en Qdrant tienen payload con tipo_procedimiento_id y version
- [ ] #3 Re-ejecutar ingesta con mismo hash es no-op o idempotente documentado
- [ ] #4 Segunda ingesta tras cambio de PDF reemplaza vectores del procedimiento
- [ ] #5 Código importa RecursiveCharacterTextSplitter y vector store LangChain verificable en repo
<!-- AC:END -->
