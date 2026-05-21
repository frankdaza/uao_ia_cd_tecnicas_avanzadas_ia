---
id: TASK-100
title: >-
  API catálogo procedimientos: subida PDF, almacenamiento y metadatos
  (UC-MVP-01)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
labels:
  - modulo-3
  - taam
  - fastapi
  - pdf
milestone: m-0
dependencies:
  - TASK-99
priority: high
ordinal: 2040
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

UC-MVP-01: el administrador registra tipos de procedimiento con PDF de recomendaciones generales. Es prerequisito de ingesta RAG y plantillas de recordatorio.

## Objetivo

Endpoints FastAPI en proyecto-2 para CRUD de `tipos_procedimiento` con upload PDF multipart.

## Endpoints sugeridos

- `POST /api/admin/procedimientos` (multipart: metadata JSON + archivo PDF)
- `GET /api/admin/procedimientos` (listado paginado)
- `GET /api/admin/procedimientos/{id}`
- `PATCH /api/admin/procedimientos/{id}` (reemplazar PDF opcional)

## Almacenamiento

- PDF en `data/taam/procedimientos/{id}/protocolo.pdf` (workspace) o volumen Docker dedicado.
- Persistir `hash_sha256` del archivo para idempotencia de re-ingesta.
- Validar: tamaño máximo (p. ej. 10 MB), MIME `application/pdf`, nombre ASCII.

## Seguridad

- Proteger con `X-Admin-Key` (mismo patrón que M2) hasta existir auth staff (TASK-105).
- No devolver ruta absoluta del servidor en respuestas JSON.

## Fallas a evitar

- Subir PDF sin registrar fila en DB (transacción: guardar archivo solo si commit OK).
- Reemplazar PDF sin incrementar `qdrant_collection_version` (TASK-101 depende de esto).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 POST multipart crea tipo_procedimiento y guarda PDF en ruta acordada
- [ ] #2 GET listado devuelve id, nombre, version_vector, fecha sin exponer secretos
- [ ] #3 Reemplazo de PDF actualiza hash y dispara campo version para reindexación
- [ ] #4 422 ante PDF inválido o campos obligatorios faltantes
- [ ] #5 Tests API con archivo PDF de fixture pequeño
<!-- AC:END -->
