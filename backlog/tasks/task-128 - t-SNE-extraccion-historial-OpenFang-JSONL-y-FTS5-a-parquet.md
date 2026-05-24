---
id: TASK-128
title: t-SNE extraccion historial OpenFang JSONL y FTS5 a parquet
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
  - TASK-122
references:
  - proyecto-3/analisis_tsne/src/extraer_jsonl.py
  - proyecto-3/analisis_tsne/README.md
  - proyecto-3/src/openfang/extraccion_tsne.py
  - proyecto-3/src/openfang/historial_jsonl.py
  - proyecto-3/docs/dashboard-openfang.md
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
modified_files:
  - proyecto-3/analisis_tsne/src/extraer_jsonl.py
  - proyecto-3/tests/analisis_tsne/test_extraer_jsonl.py
  - proyecto-3/analisis_tsne/output/.gitkeep
  - proyecto-3/src/openfang/extraccion_tsne.py
  - proyecto-3/src/openfang/marcas_tiempo.py
  - proyecto-3/src/hand/recordatorio_postoperatorio.py
  - proyecto-3/pyproject.toml
  - proyecto-3/analisis_tsne/README.md
priority: medium
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**Ruta Transversal B (bonus):** materializar el historial de interacciones del runtime OpenFang en un dataset tabular para TASK-129 (`vectorizar.py`) y el notebook t-SNE.

**Fuentes de datos (prioridad):**

1. **JSONL episodico** bajo `{OPENFANG_HOME}/sessions/` (y opcionalmente `logs/sessions.jsonl` si existe), mismo contrato que UC4/TASK-127 y [`historial_jsonl.py`](../../proyecto-3/src/openfang/historial_jsonl.py).
2. **SQLite** `{OPENFANG_HOME}/data/openfang.db`: si hay tabla virtual FTS5 enlazada a conversacion/episodica, enriquecer o recuperar turnos; si no hay FTS5 pero hay filas `memories` con `scope` episodico/conversacion, usarlas como respaldo; si no hay nada usable, continuar solo con JSONL y registrar `fts5_ausente`.

**Fuera de alcance:** embeddings (TASK-129), notebook/plotly (TASK-130), ingesta corpus RAG (`scope=semantic` de ingesta).

**Reutilizacion obligatoria:** no reimplementar lectura JSONL; extender el paquete `src.openfang` y dejar `extraer_jsonl.py` como CLI delgado.

**Referencias:** [decision-8](../decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md), [dashboard-openfang.md](../../proyecto-3/docs/dashboard-openfang.md).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `cd proyecto-3 && uv run python analisis_tsne/src/extraer_jsonl.py` escribe `analisis_tsne/output/sesiones.parquet` con columnas: `session_id`, `turno`, `rol`, `texto`, `timestamp`, `canal`
- [x] #2 **Positivo:** fixture `openfang_sesion_ejemplo.jsonl` en `sessions/` produce 3 filas; turnos de `telegram:900001` numerados 1..2 por orden temporal
- [x] #3 **Negativo:** `OPENFANG_HOME` inexistente o sin turnos conversacionales → exit != 0; stderr `openfang_home_inexistente` o `sin_datos`
- [x] #4 **Edge FTS5/SQLite:** sin `openfang.db` utilizable → exit 0 con parquet solo JSONL; log con token `fts5_ausente`
- [x] #5 Por defecto excluye `audit/hand_*.jsonl`; flag CLI `--incluir-audit` documentado
- [x] #6 Output en `analisis_tsne/output/` (gitignored salvo `.gitkeep`); dependencia `pyarrow` en `pyproject.toml`
- [x] #7 Tests en `tests/analisis_tsne/test_extraer_jsonl.py` verdes sin red
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Modulo `src/openfang/extraccion_tsne.py` (normalizar, JSONL, SQLite, fusion, turnos).
2. Refactor `src/openfang/marcas_tiempo.py` compartido con UC6.
3. CLI `analisis_tsne/src/extraer_jsonl.py` con argparse y codigos de salida estables.
4. `uv add pyarrow`; pytest `pythonpath` incluye `analisis_tsne/src`.
5. Fixtures y tests sin red; spike SQLite real documentado en notas.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- API principal: `extraccion_tsne.construir_dataframe_completo(raiz, ruta_db, ...)`.
- Spike SQLite real: `sqlite3 "$OPENFANG_HOME/data/openfang.db" ".schema"` y `SELECT name FROM sqlite_master WHERE sql LIKE '%fts%';`.
- Contrato TASK-129: una fila = un turno; agrupacion por `session_id` en `vectorizar.py`.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest tests/analisis_tsne/ -q` y `uv run ruff check` en modulos tocados
- [x] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
