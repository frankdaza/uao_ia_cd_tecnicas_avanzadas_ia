---
id: TASK-72
title: >-
  Suite de evaluación cuantitativa del RAG: golden set curado, métricas (hit@k,
  precision@k, recall@k, MRR, nDCG@k) y reporte comparativo por configuración
  (baseline → limpieza → markdown → mmr → reranker)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-14 16:30'
updated_date: '2026-05-14 22:04'
labels:
  - rag
  - qdrant
  - evaluacion
  - scripts
  - modulo-2
dependencies: []
references:
  - scripts/eval_recuperacion_consultas.py
  - config/evaluacion_rag_consultas_ejemplo.json
  - src/rag/recuperador_denso.py
  - src/rag/qdrant_store.py
  - src/api/configuracion.py
documentation:
  - .claude/skills/qa-prompt-engineering/SKILL.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: high
ordinal: 125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

### Problema

Hoy no hay termómetro cuantitativo del RAG. [`scripts/eval_recuperacion_consultas.py`](scripts/eval_recuperacion_consultas.py) imprime scores y rutas de archivos, útil para inspección manual pero **insuficiente** para decidir si un cambio mejora o empeora. Las tasks **TASK-68/69/70/71** introducen cambios estructurales (limpieza, chunking semántico, payload enriquecido, recuperación adaptativa, MMR/reranker) que **necesitan** medirse contra una referencia compartida; de lo contrario, no hay forma de validar el progreso ni de elegir defaults responsablemente.

### Objetivo

Construir un **golden set curado** y una suite de evaluación con métricas estándar de IR, y producir un **reporte comparativo** por configuración. Este artefacto se usa **antes** de TASK-68 (snapshot baseline) y **después** de cada task posterior para medir delta.

#### Componentes a entregar

1. **`data/eval/golden_set_rag.jsonl`**: ≥ 30 consultas curadas con `archivos_relevantes` (ground truth).
2. **`data/eval/golden_set.schema.json`**: JSON Schema para validación CI.
3. **`scripts/eval_metricas_rag.py`** (nuevo) o extensión sustantiva de [`scripts/eval_recuperacion_consultas.py`](scripts/eval_recuperacion_consultas.py).
4. **Métricas**: `hit@k`, `precision@k`, `recall@k`, `MRR`, `nDCG@k`. Para consultas tipo `listado/conteo` (TASK-70): métrica de cobertura (`recall_conteo` = `min(conteo_devuelto, conteo_esperado) / conteo_esperado`).
5. **Reporte Markdown** en `data/eval/reportes/eval-<fecha>-<config>.md` con tabla por consulta y tabla agregada por configuración.
6. **Comparador**: cuando se ejecuta con `--comparar reportes/eval-A.md reportes/eval-B.md`, imprime delta absoluto y relativo de cada métrica.

#### Diseño del golden set

Esquema por entrada (JSONL):

```jsonc
{
  "id": "Q001",
  "consulta": "¿Cuál es la misión institucional de la Fundación Valle del Lili?",
  "tipo": "factual",                                  // "factual" | "listado" | "conteo"
  "archivos_relevantes": [                            // ground truth: rutas relativas al repo
    "data/markdown/valledellili-org/la-fundacion-mision-y-vision.md"
  ],
  "filtros_esperados": null,                           // solo para listado/conteo
  "conteo_esperado": null,                             // solo para conteo
  "k_evaluacion": 5,
  "comentario": "Pregunta del screenshot del usuario; el chunk con la misión debe llegar al top_5."
}
```

Para `listado/conteo`:

```jsonc
{
  "id": "Q026",
  "consulta": "Lista todos los pediatras del directorio médico",
  "tipo": "listado",
  "archivos_relevantes": null,
  "filtros_esperados": {"tipo_pagina": "ficha_medico", "especialidad": "Pediatria"},
  "conteo_esperado": 100,                              // estimación con margen ±10%
  "k_evaluacion": 200
}
```

#### Distribución sugerida del golden set (≥ 30 entradas)

- **5** institucionales: misión, visión, valores, historia, dirección general.
- **5** sedes: ubicación, horarios, servicios destacados.
- **8** servicios/especialidades: gastro pediátrica, oncología adulta, cardiología, UCIP, etc.
- **5** programas: oncología, diabetes, trasplante, telemedicina, salud mental.
- **3** educación al paciente: lactancia, hipertensión, diabetes.
- **3** FAQ-like: agendar cita, contacto, urgencias.
- **3** listado/conteo (`tipo="listado"` o `tipo="conteo"`): pediatras totales, pediatras por sede, servicios oncológicos.

#### Configuraciones a comparar

| Config | Flags |
|---|---|
| `baseline` | colección actual, sin cambios |
| `limpio` | colección `corpus_fvl_v2` poblada tras TASK-68 |
| `markdown` | TASK-68 + TASK-69 |
| `mmr` | TASK-68 + TASK-69 + `RAG_MMR_HABILITADO=true` |
| `reranker` | TASK-68 + TASK-69 + MMR + `RAG_RERANKER_HABILITADO=true` |
| `adaptativo` | todo lo anterior + tool `listar_estructurado` (TASK-70) |

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [x] #1 `data/eval/golden_set_rag.jsonl` con ≥ 30 entradas, ≥ 25 factuales + ≥ 5 listado/conteo, cubriendo todas las categorías de la distribución sugerida.
- [x] #2 `data/eval/golden_set.schema.json` con JSON Schema (draft-07 o superior) validando estructura, tipos y restricciones (`archivos_relevantes` requerido si `tipo="factual"`; `filtros_esperados` y `conteo_esperado` requeridos si `tipo` en `{listado, conteo}`).
- [x] #3 Validador del schema integrado en el script (`uv run python -m scripts.eval_metricas_rag --solo-validar-golden`): no requiere red ni Qdrant; útil en CI.
- [x] #4 Métricas implementadas en `src/rag/metricas_eval.py`: `hit_at_k`, `precision_at_k`, `recall_at_k`, `mrr`, `ndcg_at_k`, `recall_conteo`. Cada una con docstring (definición) y tests unitarios en `tests/rag/test_metricas_eval.py` con ≥ 5 casos por métrica.
- [x] #5 `scripts/eval_metricas_rag.py` (nuevo módulo) ejecuta una configuración sobre todo el golden set y produce el reporte Markdown. Acepta flags: `--golden PATH`, `--config baseline|limpio|markdown|mmr|reranker|adaptativo`, `--collection NOMBRE`, `--k 5`, `--reporte-out PATH`, `--solo-validar-golden`.
- [x] #6 Reporte Markdown contiene: encabezado con timestamp y config, tabla agregada (métrica media), tabla por consulta (qid, métricas, archivos relevantes encontrados, archivos devueltos top_k), apéndice con consultas fallidas (`hit@k = 0`).
- [x] #7 Comparador `--comparar A.md B.md` imprime delta por métrica y por consulta (mejoras y regresiones), saliendo con código no-cero si alguna métrica crítica empeora más de un umbral configurable (`--umbral-regresion-mrr 0.05`).
- [x] #8 Para `tipo="listado"/"conteo"`: integración con la tool `listar_estructurado` (TASK-70) cuando esa task esté lista; mientras no exista, el evaluador degrada a "no aplicable" y lo señala en el reporte. **Esta task se entrega antes que TASK-70** para fijar baseline; la integración listado/conteo se completa en un commit posterior.
- [x] #9 Reproducible sin OpenAI: el script funciona con `EMBEDDING_PROVIDER=huggingface`, `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`, `EMBEDDING_DIMS=384`, `QDRANT_URL=:memory:` (modo de pruebas) **o** con servidor remoto.
- [x] #10 Comando documentado en `scripts/README.md`: receta completa de **baseline → mejora → comparación** con ejemplos exactos.
- [x] #11 Reporte de **baseline** ejecutado y commiteado en `data/eval/reportes/eval-baseline-<fecha>.md` (sirve como punto cero para todas las tasks posteriores).
- [x] #12 Tests del comparador en `tests/scripts/test_eval_metricas_rag.py` con dos reportes sintéticos (verifica detección de regresión y mejora).

<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->

1. **Definir el schema** `data/eval/golden_set.schema.json` (draft-07): campos obligatorios, opcionales, tipos, condicionales (`if tipo=="factual" then archivos_relevantes requerido`).
2. **Curar el golden set** `data/eval/golden_set_rag.jsonl`:
   - Recorrer manualmente cada categoría (institucional, sedes, servicios, programas, educación, FAQ, listados).
   - Para cada consulta, identificar 1–3 archivos relevantes con `rg`/búsqueda manual sobre `data/markdown/valledellili-org/`.
   - Validar contra el schema antes de mergear.
3. **Implementar métricas** en `src/rag/metricas_eval.py` (funciones puras, tipadas). Tests primero.
4. **Implementar el ejecutor** `scripts/eval_metricas_rag.py`:
   - Cargar config (baseline/limpio/...) → settings overrides → `RecuperadorDenso`.
   - Por consulta, ejecutar recuperación y calcular métricas; acumular resultados.
   - Render del reporte Markdown.
5. **Comparador**:
   - Leer dos reportes Markdown (estructura conocida) o cargar archivos JSON intermedios (`data/eval/reportes/eval-*.jsonl` con métricas por consulta antes del render).
   - Calcular delta por consulta y agregado.
   - Imprimir tabla y devolver exit code según umbral.
6. **Ejecutar baseline** sobre la colección actual y commitear el reporte.
7. **Documentar** flujo en `scripts/README.md` y nota en `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` (sección "Evaluación cuantitativa").
8. **Integración con TASK-70** (post-merge de esa task): añadir camino `tipo="listado"/"conteo"` que invoque `listar_estructurado` y calcule `recall_conteo`.

<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

### Definiciones de métricas (referencia rápida)

Sea `R_q` el conjunto de archivos relevantes para la consulta `q`, y `T_q^k` el conjunto de archivos en el top-k recuperado (deducidos a partir de `chunk.payload.archivo`).

- **`hit@k(q)`** = `1` si `T_q^k ∩ R_q ≠ ∅` else `0`.
- **`precision@k(q)`** = `|T_q^k ∩ R_q| / k`.
- **`recall@k(q)`** = `|T_q^k ∩ R_q| / |R_q|`.
- **`MRR(q)`** = `1 / rank_min(R_q ∩ T_q^k)` si hay match, else `0`.
- **`nDCG@k(q)`**: ganancia descontada normalizada con `gain(d)=1` si `d ∈ R_q`, `0` si no.
- **`recall_conteo(q)`** (solo `conteo/listado`): `min(conteo_devuelto, conteo_esperado) / conteo_esperado`, con tolerancia `±10%` documentada.

### Deduplicación por archivo

Cuando el top-k devuelve **varios chunks del mismo archivo**, contarlo **una vez** para `precision/recall` (lo importante es haber recuperado el documento relevante). Considerar también `hit_at_k_chunk` (chunk-level) como métrica auxiliar.

### Reproducibilidad

- Fijar `np.random.seed(42)` y `torch.manual_seed(42)` si se carga reranker (en TASK-71).
- Reportar versiones de dependencias en el encabezado del reporte (`uv pip list | rg "llama-index|qdrant|sentence-transformers"`).

### Estructura intermedia JSONL para el comparador

Antes del render Markdown, escribir `data/eval/reportes/eval-<fecha>-<config>.results.jsonl` con una línea por consulta:

```jsonc
{"qid": "Q001", "consulta": "...", "tipo": "factual",
 "archivos_top_k": ["..."], "hit@5": 1, "precision@5": 0.2, "recall@5": 1.0, "mrr": 1.0, "ndcg@5": 1.0}
```

Esto permite recomputar el reporte o compararlo sin re-ejecutar todo el pipeline.

### Limitaciones honestas

- Golden set pequeño (~30) tiene varianza alta; útil como termómetro, no como verdad estadística.
- `archivos_relevantes` se asigna manualmente y puede sesgar (overfit a las decisiones del curador). Mitigación: incluir comentarios y revisar entre dos personas.
- Para extender en el futuro, considerar `LLM-as-judge` para evaluar la **respuesta final** del agente (no solo la recuperación); fuera de alcance de esta task.

### Orden cronológico recomendado

1. **TASK-72 (baseline)** — esta task, antes de tocar TASK-68. Establece la línea base contra la colección actual `corpus_fvl`.
2. **TASK-68** y **TASK-69** → repoblar `corpus_fvl_v2` → reejecutar evaluación (`--config limpio`, `--config markdown`).
3. **TASK-71** → toggles de MMR/reranker → reejecutar (`--config mmr`, `--config reranker`).
4. **TASK-70** → integración listado/conteo → reejecutar (`--config adaptativo`) cubriendo Q026 a Q030.
5. Cada reporte se commitea bajo `data/eval/reportes/`.

<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [x] #1 Acceptance Criteria verificados en código, tests y documentación.
- [x] #2 `uv run pytest tests/rag/test_metricas_eval.py tests/scripts/test_eval_metricas_rag.py` pasa.
- [x] #3 Golden set commiteado, validado por schema en CI/local.
- [x] #4 Reporte baseline `data/eval/reportes/eval-baseline-<fecha>.md` commiteado.
- [x] #5 `scripts/README.md` actualizado con receta completa y comandos.
- [x] #6 `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` actualizado con sección **Evaluación cuantitativa**.
- [x] #7 Sin secretos en código, datos ni en la tarea.
- [x] #8 Al cerrar, ajustar `status` a `Done` (no archivar; ver regla `backlog-workflow.mdc`).

<!-- DOD:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->

Implementados golden set (34 entradas), schema JSON Schema draft-07, metricas puras en `src/rag/metricas_eval.py`, script `scripts/eval_metricas_rag.py` con validacion offline, corrida contra Qdrant, reporte Markdown + JSONL, comparador con umbral de regresion MRR, reporte baseline de laboratorio en `data/eval/reportes/eval-baseline-2026-05-14.md`, documentacion en `scripts/README.md` y `doc-003`. Listado/conteo marcado como N/A hasta TASK-70.

<!-- SECTION:FINAL_SUMMARY:END -->
