---
id: TASK-100
title: >-
  API catálogo procedimientos: subida PDF, almacenamiento y metadatos
  (UC-MVP-01)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
updated_date: '2026-05-21 23:14'
labels:
  - modulo-3
  - taam
  - fastapi
  - pdf
milestone: m-0
dependencies:
  - TASK-99
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC-MVP-01** ([casos de uso TAAM](../docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)): el administrador de catálogo registra un **tipo de procedimiento** con su **PDF de protocolo general** (no historial clínico por paciente). Es prerequisito de **TASK-101** (ingesta RAG → Qdrant `taam_protocolos`) y de **TASK-102** (solo procedimientos con `indexacion_estado=ok` pueden usarse en casos).

**Dependencia:** esquema y repositorios en **TASK-99** (`tipos_procedimiento`, motor async, Alembic `0001_inicial_taam`).

## Objetivo

Exponer en **`proyecto-2/`** una API administrativa REST para **alta, consulta y actualización** del catálogo `tipos_procedimiento`, incluyendo **subida multipart de PDF**, persistencia de metadatos en PostgreSQL y almacenamiento en disco bajo `data/taam/` del workspace.

## Contrato HTTP (prefijo `/api/admin`)

| Método | Ruta | Auth | Cuerpo |
| --- | --- | --- | --- |
| `POST` | `/procedimientos` | `X-Admin-Key` | `multipart/form-data`: campo `metadata` (JSON: `codigo`, `nombre`) + `archivo` (PDF) |
| `GET` | `/procedimientos` | idem | Query `limit` (1–100, default 50), `offset` (≥0) |
| `GET` | `/procedimientos/{id}` | idem | UUID |
| `PATCH` | `/procedimientos/{id}` | idem | `multipart` opcional: `metadata` JSON parcial + `archivo` PDF opcional |

**Respuesta de recurso** (sin rutas absolutas del host): `id`, `codigo`, `nombre`, `indexacion_estado`, `qdrant_collection_version`, `created_at`. No incluir `hash_pdf` ni paths de filesystem en JSON (solo uso interno / TASK-101).

## Almacenamiento y consistencia

- Ruta lógica en BD: `data/taam/procedimientos/{uuid}/protocolo.pdf` (relativa al workspace vía `resolver_ruta_workspace`).
- Tras `flush` del INSERT, escribir PDF y actualizar `ruta_pdf` + `hash_pdf` (SHA-256 hex); **rollback** de la transacción si falla validación o escritura (sin filas huérfanas ni PDFs sin fila).
- `indexacion_estado` inicial: `pendiente` (TASK-101 lo pasa a `ok`/`error`).
- **Reemplazo de PDF** (`PATCH` con archivo): recalcular hash, `indexacion_estado=pendiente`, incrementar `qdrant_collection_version` (desde `null` → `1`, luego +1).

## Validaciones

- PDF: magic `%PDF`, `Content-Type` `application/pdf`, tamaño ≤ **10 MB** (configurable), nombre de archivo **ASCII** `[A-Za-z0-9._-]+`.
- `codigo`: único, ASCII, máx. 64; `nombre`: no vacío, máx. 512.
- Errores: **422** validación; **409** código duplicado; **401/503** auth admin (patrón M2).

## Seguridad

- Cabecera **`X-Admin-Key`** + variable **`ADMIN_API_KEY`** (`src/configuracion.py`); comparación con `secrets.compare_digest`; **503** si la clave no está configurada en el servidor.
- JWT staff (**TASK-105**) puede unificar más adelante; esta tarea no lo implementa.

## Fuera de alcance

- Ingesta Qdrant (**TASK-101**), panel React (**TASK-111**), semilla demo (**TASK-114**).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `POST /api/admin/procedimientos` con multipart válido crea fila, guarda PDF en `data/taam/procedimientos/{id}/protocolo.pdf` y responde 201 con metadatos y `indexacion_estado=pendiente`
- [x] #2 `GET /api/admin/procedimientos` paginado devuelve `items` con `id`, `codigo`, `nombre`, `qdrant_collection_version`, `indexacion_estado`, `created_at` sin rutas absolutas ni secretos
- [x] #3 `GET /api/admin/procedimientos/{id}` devuelve 404 si no existe y 200 con el mismo shape que un ítem del listado
- [x] #4 `PATCH` con nuevo PDF actualiza `hash_pdf`, pone `indexacion_estado=pendiente` e incrementa `qdrant_collection_version`; `PATCH` solo metadata actualiza nombre/código sin tocar versión si no hay archivo
- [x] #5 Respuestas 422 (PDF inválido, metadata JSON inválida, campos faltantes), 409 (código duplicado), 401/503 según `ADMIN_API_KEY` / cabecera `X-Admin-Key`
- [x] #6 Tests en `proyecto-2/tests/api/` con SQLite in-memory, PDF fixture mínimo y `httpx` AsyncClient
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Dependencia:** `uv add python-multipart` en `proyecto-2/`.
2. **Config:** opcional `TAAM_PDF_MAX_MB` (default 10) en `src/configuracion.py`.
3. **Capa disco:** `src/api/servicios/almacenamiento_pdf.py` — validar PDF, SHA-256, rutas bajo `data/taam/procedimientos/{id}/`.
4. **Esquemas Pydantic:** `src/api/esquemas_procedimientos.py` (metadata, respuestas, listado).
5. **Auth:** `src/api/dependencias.py` — `requerir_clave_admin` (copiar patrón `proyecto-1/src/api/routers/admin.py`).
6. **Repositorio:** extender `RepositorioTiposProcedimiento` con `actualizar` / `contar` si hace falta paginación.
7. **Router:** `src/api/routers/admin_procedimientos.py` montado en `main.py` con prefijo `/api/admin` y lifespan DB (`session_factory`).
8. **Compose:** volumen `../data/taam` en modo lectura-escritura para permitir subida en Docker.
9. **Tests + README:** fixture PDF, casos POST/GET/PATCH/auth; `uv run pytest`; marcar AC y DoD.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Entregado: src/api/routers/admin_procedimientos.py, servicios/almacenamiento_pdf.py, dependencias.py, esquemas_procedimientos.py; main.py con lifespan BD; RepositorioTiposProcedimiento.actualizar; tests/api/test_admin_procedimientos.py (18 passed total en proyecto-2). TASK-101 debe leer hash_pdf y version para ingesta Qdrant.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
API UC-MVP-01 en proyecto-2: router admin_procedimientos (POST/GET/PATCH /api/admin/procedimientos), auth X-Admin-Key, PDF en data/taam/procedimientos/{id}/protocolo.pdf, validaciones y hash SHA-256, qdrant_collection_version al reemplazar PDF. Tests API con SQLite; README y docker-compose actualizados.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Router `/api/admin/procedimientos` registrado en `src/api/main.py` con lifespan de motor PostgreSQL/SQLite de tests
- [x] #2 `uv run pytest` en `proyecto-2/` pasa incluyendo `tests/api/test_admin_procedimientos.py`
- [x] #3 `proyecto-2/README.md` documenta endpoints, multipart, `ADMIN_API_KEY` y ruta `data/taam/procedimientos/`
- [x] #4 Sin secretos en código ni en notas de tarea; volumen Docker permite escritura en `data/taam`
<!-- DOD:END -->
