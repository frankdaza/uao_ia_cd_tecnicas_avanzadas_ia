---
id: TASK-129
title: t-SNE vectorizacion embeddings OpenAI text-embedding-3-small
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-24 16:36'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - t-sne
milestone: m-1
dependencies:
  - TASK-128
references:
  - proyecto-3/analisis_tsne/src/vectorizar.py
  - proyecto-3/src/openfang/vectorizacion_tsne.py
  - proyecto-3/src/configuracion.py
  - proyecto-3/analisis_tsne/README.md
modified_files:
  - proyecto-3/analisis_tsne/src/vectorizar.py
  - proyecto-3/src/openfang/vectorizacion_tsne.py
  - proyecto-3/tests/analisis_tsne/test_vectorizar.py
  - proyecto-3/analisis_tsne/README.md
priority: medium
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Vectorizar transcripciones (por `session_id` o por turno) con **OpenAI Embeddings** `text-embedding-3-small`; guardar `vectores.npy` + `metadatos.parquet`.

**Entrada:** `analisis_tsne/output/sesiones.parquet` (TASK-128).

**Esquema `metadatos.parquet`** (una fila por fila de `vectores.npy`, mismo orden): `indice`, `session_id`, `canal`, `turno` (nullable en modo sesión), `rol` (modo turno), `texto`, `modo` (`sesion`|`turno`), `timestamp`.

**Modo sesión (default):** ordenar por `turno` dentro de `session_id`; texto = líneas `"{rol}: {texto}"` unidas con `\n`.

**Códigos de salida:** `0` ok; `1` stderr `sin_datos` (parquet vacío o sin textos; sin llamadas API).

**CLI:** `--entrada`, `--salida-vectores`, `--salida-metadatos`, `--por-turno`, `--tam-lote` (default 32), `--modelo` (override de `OPENAI_EMBEDDING_MODEL`).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Script produce `output/vectores.npy` y `output/metadatos.parquet` alineados por índice (`len(metadatos) == vectores.shape[0]`)
- [x] #2 Flag `--por-turno` vs default por sesión documentado en README y `--help`
- [x] #3 **Negativo:** parquet vacío → no llama API; exit `1` con `sin_datos`
- [x] #4 **Edge:** rate-limit simulado → backoff exponencial (max 3 reintentos) en `embedir_lote`
- [x] #5 Tests con stub cliente OpenAI (sin red): modo sesión (2 vectores fixture), `--por-turno` (3 vectores), alineación, vacío, retry
- [x] #6 Lógica en `src/openfang/vectorizacion_tsne.py`; CLI delgado en `vectorizar.py`
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Módulo `src/openfang/vectorizacion_tsne.py` (agrupar, `embedir_lote` con retry, guardar).
2. CLI `analisis_tsne/src/vectorizar.py` con `Configuracion` y argparse.
3. Tests `tests/analisis_tsne/test_vectorizar.py` (mock, sin red).
4. README sección Vectorización.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```python
import time
import numpy as np
from openai import OpenAI

def embedir_lote(cliente: OpenAI, textos: list[str], modelo: str) -> np.ndarray:
    for intento in range(3):
        try:
            resp = cliente.embeddings.create(model=modelo, input=textos)
            return np.array([d.embedding for d in resp.data], dtype=np.float32)
        except Exception as exc:  # noqa: BLE001 — retry generico
            if intento == 2:
                raise
            time.sleep(2 ** intento)
    raise RuntimeError("no alcanzable")
```
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado pipeline de vectorizacion: modulo `src/openfang/vectorizacion_tsne.py` (agrupacion sesion/turno, embedir_lote con backoff 3 intentos, guardado npy/parquet) y CLI `analisis_tsne/src/vectorizar.py` con flags documentados. Tests: 11 passed en `tests/analisis_tsne/test_vectorizar.py` sin red (mock OpenAI). Verificacion: `cd proyecto-3 && uv run pytest tests/analisis_tsne/test_vectorizar.py -q && uv run ruff check` en archivos tocados. Salidas: `analisis_tsne/output/vectores.npy` + `metadatos.parquet` alineados por indice.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Sin API key en tests CI
- [x] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
