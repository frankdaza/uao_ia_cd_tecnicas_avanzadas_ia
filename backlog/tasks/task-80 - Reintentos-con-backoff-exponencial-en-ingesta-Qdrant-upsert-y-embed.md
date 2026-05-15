---
id: TASK-80
title: Reintentos con backoff exponencial en ingesta Qdrant (upsert y embed)
status: In Progress
assignee:
  - Frank Daza
created_date: '2026-05-14 23:29'
updated_date: '2026-05-15 00:24'
labels:
  - rag
  - qdrant
  - ingest
  - robustness
  - modulo-2
dependencies:
  - TASK-73
references:
  - scripts/indexar_corpus_qdrant.py
  - src/rag/embeddings.py
  - pyproject.toml
  - uv.lock
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
  - .claude/skills/uv-python-env/SKILL.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El script de ingesta `scripts/indexar_corpus_qdrant.py` (lineas 463-479) hace `cliente.upsert(...)` sin reintentos. Antes del upsert, llama a `embeddings.get_text_embedding_batch(...)` para obtener los vectores; tampoco hay reintentos ahi. Un blip de red, un rate limit del proveedor OpenAI o un timeout transitorio aborta **el lote completo** y exige reiniciar la ingesta desde cero (o desde el ultimo `--limit`).

En corpus grandes (cientos de archivos Markdown), esto desperdicia tiempo de embedding (coste real) y obliga a vigilar la ingesta manualmente.

## Objetivo

- Anadir reintentos con backoff exponencial a las llamadas transitorias: `embed_batch` y `upsert`.
- Distinguir errores transitorios (retry) de errores 4xx no transitorios (autenticacion, payload invalido) que no deben reintentarse.
- Permitir configurar el numero de intentos via CLI (`--reintentos N`, default 3).
- Loguear cada reintento con contexto (intento, excepcion, tamano del lote).

## Ejemplo de uso

```bash
uv run scripts/indexar_corpus_qdrant.py --reintentos 5 --backoff-max 30
```

## Alcance

Se tocan `scripts/indexar_corpus_qdrant.py`, posiblemente un nuevo modulo helper `scripts/_utiles_retry.py`, `pyproject.toml` (anadir `tenacity`) y `uv.lock`. Tests en `tests/scripts/test_ingesta_retry.py`. La reanudacion desde el ultimo lote exitoso se documenta como follow-up (no parte de esta tarea).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 pyproject.toml lista tenacity (o equivalente) como dependencia; uv.lock actualizado via uv add tenacity.
- [ ] #2 Helper _con_reintentos(callable, intentos, espera_max) o equivalente aplica backoff exponencial (intentos default 3, factor 2, espera maxima 30s).
- [ ] #3 Las llamadas a cliente.upsert(...) y embeddings.get_text_embedding_batch(...) usan el helper.
- [ ] #4 Nuevo flag CLI --reintentos N (default 3) y --backoff-max SEC (default 30) en indexar_corpus_qdrant.py.
- [ ] #5 Log estructurado por reintento: intento, tipo_excepcion, lote_id o indice del lote, espera_segundos.
- [ ] #6 Errores 4xx no transitorios (autenticacion 401/403, payload invalido 400) NO se reintentan: aborta con log de error claro.
- [ ] #7 Test unitario con FakeCliente que falla 2 veces antes de tener exito; ingesta completa con exit code 0.
- [ ] #8 Test unitario con FakeCliente que devuelve 401 -> aborta sin reintentar.
- [ ] #9 README de scripts (o seccion en README principal) documenta el flag y comportamiento.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Anadir dependencia `tenacity` (o equivalente como `backoff`) con `uv add tenacity`. Confirmar `uv.lock` actualizado.
2. Crear helper `scripts/_utiles_retry.py` (o ubicar en `src/rag/_utiles_retry.py` si se quiere reusar fuera de scripts):
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

   def _es_transitorio(exc: Exception) -> bool:
       # Filtra 401/403/400 (no transitorios) y devuelve True para resto
       if hasattr(exc, 'status_code') and exc.status_code in (400, 401, 403):
           return False
       return True

   def con_reintentos(intentos: int = 3, espera_max: float = 30.0):
       return retry(
           reraise=True,
           stop=stop_after_attempt(intentos),
           wait=wait_exponential(multiplier=1, max=espera_max),
           retry=retry_if_exception_type(Exception) & retry_if_exception(_es_transitorio),
       )
   ```
3. Modificar `scripts/indexar_corpus_qdrant.py`:
   - Anadir flags `--reintentos N` (default 3) y `--backoff-max SEC` (default 30).
   - Envolver llamadas a `embeddings.get_text_embedding_batch` y `cliente.upsert` con el helper.
   - Loguear cada reintento (tenacity expone `before_sleep` callback).
4. Tests en `tests/scripts/test_ingesta_retry.py`:
   - `test_upsert_se_reintenta_y_completa`: `FakeCliente.upsert` lanza `ConnectionError` 2 veces y luego completa; aserrar 3 llamadas, exit 0.
   - `test_upsert_no_transitorio_aborta`: `FakeCliente.upsert` lanza `RequestError(status_code=401)`; aserrar 1 sola llamada y exit != 0.
   - `test_embed_se_reintenta`: simular timeout en `get_text_embedding_batch`.
5. Anadir seccion en `README.md` (o crear `scripts/README.md`) documentando los flags.
6. Correr ingesta manual contra Qdrant local con corpus reducido para validar.
7. Marcar AC/DoD; `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Distinguir transitorios vs no transitorios es clave: 4xx no se debe reintentar (gasta cuota); 5xx, ConnectionError, TimeoutError si. La libreria `tenacity` permite combinar `retry_if_exception_type` con un predicado custom. Si la libreria `qdrant-client` ya tiene reintentos internos, configurar este wrapper para no duplicar (revisar `QdrantClient(timeout=...)`). La reanudacion desde el ultimo lote exitoso se deja como follow-up (TASK futura). TASK-82 anadira `--fail-if-empty` a la eval; mantener coherencia de flags entre scripts.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv sync instala tenacity sin errores.
- [ ] #2 uv run pytest tests/scripts/test_ingesta_retry.py -v en verde.
- [ ] #3 Ingesta manual contra Qdrant local exitosa con --reintentos 3.
- [ ] #4 Tarea con status: Done sin archivar.
<!-- DOD:END -->
