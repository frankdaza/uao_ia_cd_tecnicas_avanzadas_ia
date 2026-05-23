---
id: TASK-101
title: >-
  Ingesta PDF a vector store LangChain (RecursiveCharacterTextSplitter, Qdrant
  TAAM)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
updated_date: '2026-05-21 23:21'
labels:
  - modulo-3
  - taam
  - rag
  - langchain
milestone: m-0
dependencies:
  - TASK-100
references:
  - >-
    backlog/decisions/decision-7 -
    Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md
  - >-
    backlog/tasks/task-100 -
    API-catálogo-procedimientos-subida-PDF-almacenamiento-y-metadatos-UC-MVP-01.md
documentation:
  - >-
    backlog/docs/actividades/Actividad del Módulo 3_ Productización, Despliegue
    Avanzado y Sistemas Agénticos.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC-MVP-01** ([casos de uso TAAM](../docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)): tras **TASK-100**, cada `tipos_procedimiento` tiene PDF en `data/taam/procedimientos/{id}/protocolo.pdf`, `hash_pdf` y `indexacion_estado=pendiente`. Esta tarea materializa el protocolo en **Qdrant** para RAG del agente M3 (**decision-7**): stack **LangChain nativo** (`RecursiveCharacterTextSplitter` + vector store), **sin** LlamaIndex en runtime ni colección M2 `corpus_*`.

**Dependencias:** TASK-100 (API + disco + campos `hash_pdf`, `qdrant_collection_version`). TASK-102 exige `indexacion_estado=ok` para activar casos.

## Objetivo

1. **Script CLI** `proyecto-2/scripts/ingestar_protocolo_pdf.py` (`uv run python -m scripts.ingestar_protocolo_pdf`) para operadores y CI.
2. **Servicio reutilizable** `src/ingesta/protocolo_pdf.py` invocable desde la API admin tras `POST`/`PATCH` con PDF.
3. Actualizar `indexacion_estado` (`ok` | `error`) y mantener `qdrant_collection_version` coherente con los vectores.

## Diseño técnico

| Paso | Detalle |
| --- | --- |
| Extracción | **pdfplumber** por página → `Document` LangChain con metadata `pagina`, `nombre_archivo`. PDF escaneado sin OCR → poco texto: marcar `error` y log claro (limitación UC). |
| Chunking | `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)` — rubrica M3 / decision-7. |
| Embeddings | `OpenAIEmbeddings` (`OPENAI_API_KEY`, modelo configurable p. ej. `text-embedding-3-small`). |
| Vector store | `langchain_qdrant.QdrantVectorStore`, colección **`taam_protocolos`**, distancia **Cosine**, URL `QDRANT_URL` (host **6334** en dev). |
| Payload Qdrant | `tipo_procedimiento_id`, `pagina`, `nombre_archivo`, `version` (int = `qdrant_collection_version`), `hash_pdf`, `chunk_index`. |
| Idempotencia | Si `hash_pdf` coincide con el ya indexado y `indexacion_estado=ok` → **no-op** (log + salida 0). |
| Re-ingesta | Antes de upsert: **borrar** todos los puntos con `tipo_procedimiento_id` igual (filtro Qdrant); luego upsert chunks de la versión actual. Cambio de PDF (PATCH) incrementa versión en TASK-100 → nueva ingesta reemplaza vectores. |
| Reintentos | Backoff exponencial en embed/upsert (patrón task-80 / `_utiles_retry`), sin reintentar 400/401/403. |

## Integración API

Tras `POST` o `PATCH` con archivo PDF (respuesta **201/200** ya persistida), disparar ingesta en **BackgroundTasks** de FastAPI (no bloquear la respuesta HTTP). Si falla: `indexacion_estado=error`; si ok: `ok`. Timeout interno acotado (p. ej. 120 s) por procedimiento.

Endpoint opcional admin `POST /api/admin/procedimientos/{id}/reindexar` para relanzar manualmente (misma lógica que el script).

## Fuera de alcance

- Tool RAG en runtime del agente (**TASK-103+**).
- OCR de PDF escaneados.
- Compartir instancia/colección Qdrant con M2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 `uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid>` indexa un PDF de prueba, imprime estadísticas (páginas, chunks, versión) y deja `indexacion_estado=ok` en Postgres
- [x] #2 #2 Puntos en Qdrant colección `taam_protocolos` incluyen payload `tipo_procedimiento_id`, `version`, `pagina`, `nombre_archivo` (verificable con filtro o scroll en test/integration)
- [x] #3 #3 Re-ejecutar ingesta con el mismo `hash_pdf` y estado `ok` es no-op documentado (0 upserts, log explícito)
- [x] #4 #4 Tras `PATCH` con PDF distinto (nuevo hash, versión incrementada), la ingesta elimina vectores previos del `tipo_procedimiento_id` y solo quedan chunks de la versión nueva
- [x] #5 #5 El repo contiene `RecursiveCharacterTextSplitter` y uso de vector store LangChain (`langchain_qdrant` / `QdrantVectorStore`) bajo `proyecto-2/`
- [x] #6 #6 Tras `POST /api/admin/procedimientos` válido, la ingesta en background actualiza el estado a `ok` o `error` (test con dependencias mockeadas o integración documentada)
- [x] #7 #7 Tests en `proyecto-2/tests/` cubren splitter/idempotencia lógica y al menos un flujo de servicio con Qdrant `:memory:` o cliente mockeado
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Dependencias** — `uv add langchain-text-splitters langchain-core langchain-openai langchain-qdrant qdrant-client pdfplumber tenacity`.
2. **Config** — En `src/configuracion.py`: `taam_qdrant_collection` (default `taam_protocolos`), `taam_chunk_size` (800), `taam_chunk_overlap` (120), `embedding_model`, flags de reintentos; actualizar `.env.example`.
3. **Reintentos** — `src/ingesta/reintentos.py` (copiar política task-80).
4. **Núcleo** — `src/ingesta/protocolo_pdf.py`: extraer texto, split, borrar por filtro, `add_documents` con metadatos, actualizar fila OLTP.
5. **Vector store** — `src/rag/vector_store.py`: factory `QdrantVectorStore` + asegurar colección.
6. **CLI** — `scripts/ingestar_protocolo_pdf.py` (`--tipo-id`, `--todos-pendientes`, `--reintentos`).
7. **API** — `src/api/servicios/ingesta_protocolo.py` + BackgroundTasks en `admin_procedimientos.py`; opcional `POST .../reindexar`.
8. **Tests** — `tests/ingesta/test_protocolo_pdf.py` (splitter, no-op hash, delete+upsert mock); ampliar `tests/api/` si aplica.
9. **Cierre** — pytest verde, marcar AC/DoD, `status: Done`, notas de implementación.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Entregado: src/ingesta/protocolo_pdf.py (pdfplumber, RecursiveCharacterTextSplitter 800/120, idempotencia ok+hash, delete por tipo_procedimiento_id), src/rag/vector_store.py (QdrantVectorStore + OpenAIEmbeddings), src/ingesta/reintentos.py, scripts/ingestar_protocolo_pdf.py, API BackgroundTasks tras POST/PATCH PDF y POST .../reindexar, configuracion TAAM_QDRANT_COLLECTION y chunking. Tests: tests/ingesta/test_protocolo_pdf.py, tests/api/test_ingesta_background.py. uv run pytest: 24 passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Ingesta PDF TAAM con LangChain (RecursiveCharacterTextSplitter + QdrantVectorStore coleccion taam_protocolos), script CLI, disparo en background desde API admin y tests pytest en proyecto-2.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 #1 `uv add` registra dependencias LangChain/Qdrant/pdfplumber/tenacity; `uv.lock` versionado
- [x] #2 #2 `proyecto-2/README.md` y `scripts/README.md` documentan CLI, variables (`QDRANT_URL`, `OPENAI_API_KEY`, chunking) y limitación PDF sin OCR
- [x] #3 #3 `uv run pytest` en `proyecto-2/` pasa incluyendo tests nuevos de ingesta
- [x] #4 #4 `rg 'RecursiveCharacterTextSplitter' proyecto-2` y `rg 'QdrantVectorStore|langchain_qdrant' proyecto-2` encuentran coincidencias
- [x] #5 #5 Sin mezclar colección `corpus_*` de M2; sin secretos en backlog ni código
<!-- DOD:END -->
