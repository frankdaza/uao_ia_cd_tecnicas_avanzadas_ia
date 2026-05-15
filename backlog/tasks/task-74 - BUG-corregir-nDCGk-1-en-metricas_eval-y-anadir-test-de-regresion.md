---
id: TASK-74
title: 'BUG: corregir nDCG@k > 1 en metricas_eval y anadir test de regresion'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-14 23:25'
updated_date: '2026-05-15 00:07'
labels:
  - rag
  - evaluation
  - bug
  - modulo-2
dependencies:
  - TASK-73
references:
  - src/rag/metricas_eval.py
  - tests/rag/test_metricas_eval.py
  - scripts/eval_metricas_rag.py
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
modified_files:
  - src/rag/metricas_eval.py
  - tests/rag/test_metricas_eval.py
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La auditoria del pipeline RAG detecto que `ndcg_at_k` en `src/rag/metricas_eval.py` (lineas 93-115) viola la definicion clasica de nDCG: puede devolver valores **mayores que 1.0**.

## Detalle del bug

El DCG suma ganancia binaria 1 **por cada chunk** cuyo `archivo` esta en el conjunto de relevantes `R`. Pero el iDCG esta acotado a `min(k, |R|)` donde `|R|` cuenta **documentos unicos**. Si en el top-k aparecen multiples chunks del **mismo** documento relevante, **DCG > iDCG** y por tanto **nDCG > 1**, lo cual viola la definicion (`0 <= nDCG <= 1`).

### Ejemplo reproducible

```python
relevantes = {"docs/mision.md"}  # |R| = 1
top_k = [
    "docs/mision.md#chunk-0",
    "docs/mision.md#chunk-1",
    "docs/mision.md#chunk-2",
    "docs/otros.md#chunk-0",
    "docs/otros.md#chunk-1",
]
# DCG = 1/log2(2) + 1/log2(3) + 1/log2(4) = 1.0 + 0.6309 + 0.5 = 2.131
# iDCG actual = sum(1/log2(i+1) for i in range(1, min(5,1)+1)) = 1.0
# nDCG = 2.131 > 1.0  (BUG)
```

## Decision de granularidad

Alineado con TASK-73, la metrica `nDCG@k` queda definida **por chunk** con relevancia binaria. El iDCG ideal es la situacion en la que las primeras `k` posiciones son todas relevantes, por lo que:

```
idcg = sum(1.0 / log2(i + 2) for i in range(k))
```

y `nDCG = DCG / iDCG` queda acotado a `[0, 1]`.

Alternativa descartada: nDCG por documento deduplicado (`list(dict.fromkeys(top_k))` antes del calculo, iDCG con `min(k, |R|)`). Mas conservadora pero pierde resolucion cuando un solo documento responde varias posiciones del ranking. Si el equipo prefiere esa opcion, documentarlo en doc-003 y ajustar la implementacion.

## Impacto

- Reportes historicos pueden cambiar; queda en TASK-82 anadir el `git rev-parse` al contexto del reporte para trazabilidad.
- No cambia la API publica de `metricas_eval`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ndcg_at_k devuelve siempre 0.0 <= ndcg <= 1.0 para cualquier top_k y conjunto de relevantes (incluyendo casos con un solo documento relevante repetido en multiples chunks).
- [x] #2 Test parametrizado nuevo en tests/rag/test_metricas_eval.py cubre: (a) un solo doc relevante repetido en k chunks; (b) lista de relevantes vacia; (c) k=0; (d) ningun chunk relevante; (e) todos chunks relevantes; (f) mezcla de relevantes y no relevantes.
- [x] #3 doc-003 queda alineado a la definicion elegida (nDCG por chunk con iDCG acotado a k); TASK-73 ya separo granularidades, aqui solo se indica cual aplica a nDCG.
- [x] #4 scripts/eval_metricas_rag.py no cambia su CLI; corridas con --config baseline producen nDCG <= 1.
- [x] #5 No se rompen tests existentes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Confirmar con TASK-73 ya aplicada que la definicion en doc-003 corresponde a nDCG por chunk con iDCG acotado a k.
2. Reescribir `ndcg_at_k` en `src/rag/metricas_eval.py`:
   ```python
   def ndcg_at_k(top_k_archivos: list[str], relevantes: set[str], k: int) -> float:
       if k <= 0 or not relevantes:
           return 0.0
       posiciones = top_k_archivos[:k]
       dcg = sum(
           1.0 / math.log2(i + 2)
           for i, archivo in enumerate(posiciones)
           if archivo in relevantes
       )
       idcg = sum(1.0 / math.log2(i + 2) for i in range(k))
       return dcg / idcg if idcg > 0 else 0.0
   ```
3. Anadir tests parametrizados en `tests/rag/test_metricas_eval.py`:
   - Caso (a): un solo doc relevante con k chunks repetidos -> nDCG > 0 pero <= 1.
   - Caso (b): relevantes vacio -> 0.0.
   - Caso (c): k = 0 -> 0.0.
   - Caso (d): ningun chunk relevante -> 0.0.
   - Caso (e): todos chunks relevantes -> nDCG == 1.0.
   - Caso (f): mezcla -> 0 < nDCG < 1.
4. Correr `uv run pytest tests/rag/test_metricas_eval.py -v` y confirmar verde.
5. Correr `uv run scripts/eval_metricas_rag.py --config baseline` y confirmar que el reporte muestra `nDCG@k <= 1`.
6. Marcar AC y DoD; dejar `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Mantener firma publica y nombre `ndcg_at_k` para no romper imports existentes. Si el equipo prefiere la alternativa (nDCG por documento deduplicado), ajustar el plan y documentar en doc-003 (esta tarea sigue siendo valida con la alternativa: solo cambia la implementacion del DCG y la cota de iDCG). El test de regresion del caso (a) es la clave: con la implementacion previa fallaria por nDCG > 1; con la nueva pasa.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se corrigio `ndcg_at_k` para usar iDCG con suma sobre las k ranuras (todas relevantes en el ranking ideal), garantizando 0 <= nDCG <= 1 cuando R no es vacio. Se anadio `if not rel: return 0.0`. Tests: ajuste de expectativas en `TestNdcgAtK` y prueba parametrizada TASK-74 (casos a-f). doc-003: fila nDCG alineada a la definicion. `uv run pytest tests/rag/test_metricas_eval.py -v` y `tests/rag/` en verde. Eval `uv run python -m scripts.eval_metricas_rag --config baseline` ejecutado con Qdrant local (docker compose); nDCG@k en reporte <= 1. Artefactos de reporte generados se eliminaron del arbol de trabajo para no dejar archivos sin seguimiento.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv run pytest tests/rag/test_metricas_eval.py -v en verde.
- [x] #2 uv run scripts/eval_metricas_rag.py --config baseline manualmente exitoso con nDCG <= 1.
- [x] #3 Tarea con status: Done sin archivar.
<!-- DOD:END -->
