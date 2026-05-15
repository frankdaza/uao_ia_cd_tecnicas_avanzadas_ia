---
id: TASK-82
title: >-
  Eval RAG multi-config en una corrida + guardarrailes (fail-if-empty, git rev,
  umbrales recall/nDCG)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-14 23:31'
updated_date: '2026-05-15 00:44'
labels:
  - rag
  - evaluation
  - ci
  - modulo-2
dependencies:
  - TASK-74
  - TASK-77
  - TASK-78
  - TASK-79
  - TASK-80
references:
  - scripts/eval_metricas_rag.py
  - scripts/eval_recuperacion_consultas.py
  - src/rag/qdrant_store.py
  - src/rag/metricas_eval.py
  - >-
    backlog/tasks/task-72 -
    Suite-evaluacion-cuantitativa-RAG-golden-set-metricas-reporte.md
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La auditoria identifico tres limitaciones del flujo de evaluacion RAG en `scripts/eval_metricas_rag.py`:

1. **Una sola config por corrida**. El script solo permite `--config X` por invocacion (lineas 456-558); comparar `baseline / mmr / reranker / combinado` exige varias ejecuciones manuales y luego usar `--comparar` que solo une dos `.results.jsonl`.
2. **Colecciones vacias no fallan**. `asegurar_coleccion` (`src/rag/qdrant_store.py`) crea la coleccion si no existe (lineas 519-525 de eval), la evaluacion reporta metricas cercanas a 0 sin error claro.
3. **Guardarrailes pobres**. `--comparar` evalua regresion solo con MRR (lineas 404-410); no hay umbral sobre recall@k ni nDCG. La reproducibilidad esta incompleta: el reporte no incluye `git rev-parse HEAD`, SHA256 del golden, ni firma del modelo de embeddings.

## Objetivo

- Implementar `--config todas` que ejecute los 4 presets (`baseline / mmr / reranker / combinado`) en una sola corrida y produzca un reporte consolidado y un CSV comparable.
- Anadir `--fail-if-empty`: aborta con exit code distinto de 0 si la coleccion Qdrant esta vacia o no existe.
- Anadir flags de umbrales en `--comparar`: `--umbral-mrr`, `--umbral-recall-k`, `--umbral-ndcg-k`; falla si cualquiera regresa.
- Enriquecer 'Contexto de ejecucion' del reporte: commit git (rev-parse HEAD), timestamp UTC, modelo embeddings, modelo reranker, defaults de Configuracion relevantes, SHA256 del golden file.

## Ejemplo de uso

```bash
uv run scripts/eval_metricas_rag.py --config todas --fail-if-empty
uv run scripts/eval_metricas_rag.py --comparar antes.jsonl despues.jsonl --umbral-mrr -0.01 --umbral-recall-k -0.02
```

## Alcance

Se tocan `scripts/eval_metricas_rag.py` (logica multi-config, guardarrailes, contexto), `src/rag/qdrant_store.py` (helper conteo no-creador), opcionalmente `src/rag/metricas_eval.py` (helper de comparacion). Tests en `tests/scripts/test_eval_metricas_rag.py` con golden minimo y `FakeRecuperador`. CI/workflow puede consumir `--fail-if-empty` para validar ingesta.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 uv run scripts/eval_metricas_rag.py --config todas ejecuta los 4 presets en una sola corrida y escribe: (a) reporte consolidado en reportes/eval_rag_<timestamp>.md; (b) CSV con metricas comparables por preset (reportes/eval_rag_<timestamp>.csv).
- [x] #2 Flag --fail-if-empty aborta con exit code distinto de 0 si la coleccion Qdrant esta vacia o no existe. Validar via cliente.count(collection_name=..., exact=False).
- [x] #3 --comparar admite umbrales: --umbral-mrr (default 0.0), --umbral-recall-k (default 0.0), --umbral-ndcg-k (default 0.0); falla si cualquiera regresa por debajo del umbral.
- [x] #4 Seccion 'Contexto de ejecucion' del reporte incluye: commit git (subprocess git rev-parse HEAD), timestamp UTC, modelo embeddings (provider + nombre), modelo reranker (si activo), defaults Configuracion relevantes (top_k, mmr_lambda, etc.), SHA256 del golden file.
- [x] #5 Tests de pytest con tmp_path y mocks: (a) --config todas produce reporte; (b) --fail-if-empty con coleccion vacia exit 1; (c) --comparar con regresion sobre umbral falla.
- [x] #6 Back-compat: --config baseline (y otros presets individuales) siguen funcionando para no romper scripts/Makefile existentes.
- [x] #7 El CSV es UTF-8 sin BOM (o con BOM opcional) y se abre limpio en pandas/Excel.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Refactor `scripts/eval_metricas_rag.py` para iterar presets cuando `--config todas`:
   - Renombrar la logica actual a `_ejecutar_un_preset(config_name) -> ResultadosPreset`.
   - Si `--config == 'todas'`, llamar `_ejecutar_un_preset` para `['baseline', 'mmr', 'reranker', 'combinado']` en serie y agregar resultados.
   - Escribir reporte md unico con secciones por preset + tabla comparativa.
   - Escribir CSV con columnas: `preset, query_id, hit@5, mrr, recall@10, ndcg@10, ...`.
2. Anadir `--fail-if-empty`:
   - Antes de evaluar, llamar `cliente.count(collection_name=cfg.qdrant_collection, exact=False).count`.
   - Si `count == 0`, log error claro (`coleccion {nombre} vacia: ejecuta scripts/indexar_corpus_qdrant.py`) y `sys.exit(1)`.
3. Anadir flags `--umbral-mrr`, `--umbral-recall-k`, `--umbral-ndcg-k` a `--comparar`:
   ```python
   parser.add_argument('--umbral-mrr', type=float, default=0.0)
   parser.add_argument('--umbral-recall-k', type=float, default=0.0)
   parser.add_argument('--umbral-ndcg-k', type=float, default=0.0)
   ```
   En la logica de comparacion, calcular delta de cada metrica y comparar contra los umbrales. Si alguno regresa, `sys.exit(1)` con mensaje.
4. Enriquecer la seccion 'Contexto de ejecucion' del reporte:
   ```python
   commit = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
   golden_hash = hashlib.sha256(Path(args.golden).read_bytes()).hexdigest()
   ```
   Anadir al markdown: `**Commit**: {commit}`, `**Golden SHA256**: {golden_hash}`, `**Embeddings**: {provider}/{nombre}`, `**Reranker**: {modelo if activo else 'off'}`, `**Defaults**: {tabla}`.
5. Tests en `tests/scripts/test_eval_metricas_rag.py`:
   - `test_config_todas_produce_reporte`: con `FakeRecuperador` y golden minimo en `tmp_path`, aserrar que el reporte y CSV existen y tienen las 4 secciones.
   - `test_fail_if_empty_aborta_con_coleccion_vacia`: mock `cliente.count.return_value.count = 0`, aserrar `sys.exit(1)`.
   - `test_comparar_umbral_mrr_falla`: dos jsonl con regresion de MRR > umbral, aserrar exit 1.
6. Actualizar README o `scripts/README.md` con ejemplos de uso de los nuevos flags.
7. Marcar AC/DoD; `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Mantener back-compat: `--config baseline` sigue funcionando para evitar romper scripts existentes. El CSV debe permitir abrir limpio en pandas/Excel; UTF-8 BOM opcional (Excel lo prefiere para acentos). Si se anade dependencia para tablas (p. ej. `tabulate`), declararla con `uv add`. Considerar generar grafico simple (matplotlib) opcional con `--grafico`, pero queda fuera del alcance estricto. El golden hash SHA256 da trazabilidad de que set se uso. TASK-83 anadira tests de regresion mas amplios; aqui solo los del propio script.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado: (1) --config todas ejecuta baseline/mmr/reranker/combinado y escribe data/eval/reportes/eval_rag_<timestampUTC>.{md,csv,results.jsonl} con columna preset en CSV/JSONL; (2) contar_puntos_en_coleccion en qdrant_store + --fail-if-empty con exit 1 si coleccion ausente o vacia; (3) --comparar con --umbral-mrr, --umbral-recall-k, --umbral-ndcg-k (default 0) y compatibilidad --umbral-regresion-mrr (equivale a umbral MRR negado); (4) contexto de reporte enriquecido con commit git, SHA256 del golden, embeddings/reranker y defaults; (5) tests en tests/scripts/test_eval_metricas_rag.py; (6) presets individuales sin cambio de contrato; (7) CSV UTF-8 sin BOM. Documentacion actualizada en scripts/README.md.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv run pytest tests/scripts/test_eval_metricas_rag.py -v en verde.
- [x] #2 Corrida manual uv run scripts/eval_metricas_rag.py --config todas produce reporte + CSV.
- [x] #3 Corrida manual con coleccion vacia y --fail-if-empty exit 1.
- [x] #4 Tarea con status: Done sin archivar.
<!-- DOD:END -->
