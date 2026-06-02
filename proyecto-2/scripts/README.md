# Scripts TAAM

## Ingesta de protocolos (PDF o Markdown) → Qdrant

El CLI historico `ingestar_protocolo_pdf` indexa segun `formato_protocolo` y `ruta_pdf` en BD (`.pdf` o `.md`).

```bash
cd proyecto-2
# Un procedimiento (UUID de tipos_procedimiento)
uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid>

# Todos con indexacion_estado=pendiente
uv run python -m scripts.ingestar_protocolo_pdf --todos-pendientes

# Re-indexar aunque ya este en ok (mismo hash)
uv run python -m scripts.ingestar_protocolo_pdf --tipo-id <uuid> --forzar
```

**Requisitos:** Postgres TAAM migrado (`alembic upgrade head`, revision `0004_formato_protocolo_taam` para Markdown), Qdrant en `QDRANT_URL` (p. ej. `http://127.0.0.1:6334`), `OPENAI_API_KEY` para embeddings.

**Variables:** `TAAM_QDRANT_COLLECTION` (default `taam_protocolos`), `TAAM_CHUNK_SIZE` (800), `TAAM_CHUNK_OVERLAP` (120), `TAAM_PDF_MAX_MB` (tamano maximo de subida PDF y MD), `EMBEDDING_MODEL`, `INGESTA_REINTENTOS`, `INGESTA_BACKOFF_MAX_SEG`.

**Notas:**

- PDFs escaneados sin OCR suelen producir poco texto → `indexacion_estado=error`.
- Markdown con front matter YAML invalido se rechaza en el upload (422); cuerpo vacio tras front matter valido → `error` tras la ingesta.

**Subida equivalente (API admin):**

```bash
export ADMIN_API_KEY='su-clave'

curl -sS -H "X-Admin-Key: $ADMIN_API_KEY" \
  -F 'metadata={"codigo":"demo-pdf","nombre":"Protocolo PDF"};type=application/json' \
  -F "archivo=@protocolo.pdf;type=application/pdf" \
  http://127.0.0.1:8001/api/admin/procedimientos

curl -sS -H "X-Admin-Key: $ADMIN_API_KEY" \
  -F 'metadata={"codigo":"demo-md","nombre":"Protocolo Markdown"};type=application/json' \
  -F "archivo=@protocolo.md;type=text/markdown" \
  http://127.0.0.1:8001/api/admin/procedimientos
```

## Demo TAAM (TASK-114)

Tras migraciones y `STAFF_JWT_SECRET` en `.env`.

**Arranque automatico (Docker):** en `proyecto-2/.env`:

```env
TAAM_SEMBRAR_DEMO_HABILITADO=true
OPENAI_API_KEY=sk-...   # requerido si TAAM_SEMBRAR_DEMO_CON_INGESTA=true (default)
# TAAM_SEMBRAR_DEMO_CON_INGESTA=false   # sembrar sin indexar Qdrant
```

Con `docker compose up`, el entrypoint ejecuta `sembrar_demo_taam` tras Alembic (con `--con-ingesta` por defecto).

**Manual:**

```bash
cd proyecto-2
uv run python -m scripts.sembrar_demo_taam
uv run python -m scripts.sembrar_demo_taam --con-ingesta
uv run python -m scripts.sembrar_demo_taam --sin-conversacion
```

Deja procedimiento `COLE-LAP-001`, casos `PAC-DEMO-001` / `PAC-DEMO-002`, alerta urgente y codigo `DEMO2X`. Guion: [GUION-DEMO-TAAM.md](../../backlog/docs/usecases/GUION-DEMO-TAAM.md).
