# Scripts TAAM

## Ingesta de protocolos PDF → Qdrant

```bash
cd proyecto-2
# Un procedimiento (UUID de tipos_procedimiento)
uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid>

# Todos con indexacion_estado=pendiente
uv run python -m scripts.ingestar_protocolo_pdf --todos-pendientes

# Re-indexar aunque ya este en ok (mismo hash)
uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid> --forzar
```

**Requisitos:** Postgres TAAM migrado, Qdrant en `QDRANT_URL` (p. ej. `http://127.0.0.1:6334`), `OPENAI_API_KEY` para embeddings.

**Variables:** `TAAM_QDRANT_COLLECTION` (default `taam_protocolos`), `TAAM_CHUNK_SIZE` (800), `TAAM_CHUNK_OVERLAP` (120), `EMBEDDING_MODEL`, `INGESTA_REINTENTOS`, `INGESTA_BACKOFF_MAX_SEG`.

**Nota:** PDFs escaneados sin OCR suelen producir poco texto; el script marca `indexacion_estado=error` en ese caso.

## Demo TAAM (TASK-114)

Tras migraciones y `STAFF_JWT_SECRET` en `.env`:

```bash
cd proyecto-2
uv run python -m scripts.sembrar_demo_taam
uv run python -m scripts.sembrar_demo_taam --con-ingesta   # opcional Qdrant
uv run python -m scripts.sembrar_demo_taam --sin-conversacion
```

Deja procedimiento `COLE-LAP-001`, casos `PAC-DEMO-001` / `PAC-DEMO-002`, alerta urgente y codigo `DEMO2X`. Guion: [GUION-DEMO-TAAM.md](../../backlog/docs/usecases/GUION-DEMO-TAAM.md).
