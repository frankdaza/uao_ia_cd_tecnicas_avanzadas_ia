---
id: TASK-128
title: t-SNE extraccion historial OpenFang JSONL y FTS5 a parquet
status: In Progress
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-23 17:22'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - t-sne
milestone: m-1
dependencies:
  - TASK-122
references:
  - proyecto-3/analisis_tsne/src/extraer_jsonl.py
  - proyecto-3/analisis_tsne/README.md
modified_files:
  - proyecto-3/analisis_tsne/src/extraer_jsonl.py
  - proyecto-3/tests/analisis_tsne/test_extraer_jsonl.py
  - proyecto-3/analisis_tsne/output/.gitkeep
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**Ruta Transversal B:** extraer turnos de conversación desde JSONL y SQLite FTS5 de OpenFang hacia `analisis_tsne/output/sesiones.parquet` para el pipeline de embeddings.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `uv run python analisis_tsne/src/extraer_jsonl.py` genera parquet con columnas: `session_id`, `turno`, `rol`, `texto`, `timestamp`, `canal`
- [ ] #2 **Positivo:** fixture JSONL sintético produce ≥3 filas esperadas
- [ ] #3 **Negativo:** ruta JSONL ausente → exit ≠ 0, mensaje `archivo_no_encontrado`
- [ ] #4 **Edge:** si SQLite FTS5 no existe, script continúa solo con JSONL y log `fts5_ausente`
- [ ] #5 Output en `analisis_tsne/output/` (gitignored salvo `.gitkeep`)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Implementar parser línea a línea JSONL.
2. Opcional: conexión `sqlite3` a FTS5.
3. Normalizar a DataFrame pandas → parquet.
4. Fixtures y tests sin red.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```python
import json
from pathlib import Path
import pandas as pd

def extraer_jsonl(ruta: Path) -> pd.DataFrame:
    filas = []
    with ruta.open(encoding="utf-8") as f:
        for linea in f:
            if not linea.strip():
                continue
            ev = json.loads(linea)
            filas.append({
                "session_id": ev.get("session_id"),
                "turno": ev.get("turn", ev.get("turno")),
                "rol": ev.get("role", ev.get("rol")),
                "texto": ev.get("content", ev.get("texto", "")),
                "timestamp": ev.get("ts", ev.get("timestamp")),
                "canal": ev.get("channel", "telegram"),
            })
    return pd.DataFrame(filas)
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Tests pytest verdes
- [ ] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
