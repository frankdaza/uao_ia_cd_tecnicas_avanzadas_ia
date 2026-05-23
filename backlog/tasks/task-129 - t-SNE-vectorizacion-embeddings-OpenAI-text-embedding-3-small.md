---
id: TASK-129
title: 't-SNE vectorizacion embeddings OpenAI text-embedding-3-small'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
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
  - proyecto-3/src/configuracion.py
modified_files:
  - proyecto-3/analisis_tsne/src/vectorizar.py
  - proyecto-3/tests/analisis_tsne/test_vectorizar.py
priority: medium
ordinal: 1290
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Vectorizar transcripciones (por `session_id` o por turno) con **OpenAI Embeddings** `text-embedding-3-small`; guardar `vectores.npy` + `metadatos.parquet`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Script produce `output/vectores.npy` y `output/metadatos.parquet` alineados por índice
- [ ] #2 Flag `--por-turno` vs default por sesión documentado
- [ ] #3 **Negativo:** parquet vacío → no llama API; exit con `sin_datos`
- [ ] #4 **Edge:** rate-limit simulado → backoff exponencial (max 3 reintentos) en código
- [ ] #5 Tests con stub cliente OpenAI (sin red)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Cargar parquet de task-128.
2. Agrupar texto por sesión o turno.
3. Cliente `openai` con `Settings`.
4. Guardar artefactos numpy/pandas.
5. Tests mock.
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

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Sin API key en tests CI
- [ ] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
