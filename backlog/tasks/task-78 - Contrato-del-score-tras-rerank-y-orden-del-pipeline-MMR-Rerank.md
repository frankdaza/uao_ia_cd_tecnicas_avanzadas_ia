---
id: TASK-78
title: Contrato del score tras rerank y orden del pipeline MMR/Rerank
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-14 23:28'
updated_date: '2026-05-14 23:28'
labels:
  - rag
  - reranker
  - mmr
  - correctness
  - modulo-2
dependencies:
  - TASK-75
  - TASK-76
  - TASK-77
references:
  - src/rag/recuperador_denso.py
  - src/rag/reranker_cross_encoder.py
  - src/rag/diversificador_mmr.py
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
  - tests/rag/test_recuperador_denso_pipeline.py
  - scripts/eval_metricas_rag.py
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
priority: medium
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La auditoria detecto dos problemas relacionados con el orden del pipeline y la semantica del score visible a consumidores:

### Problema 1: contrato del score

En `src/rag/recuperador_denso.py` (lineas 45-51, 302-328), tras el reranker el campo `FuenteRagDenso.score` queda con el **score del cross-encoder** (logit no normalizado), pero el docstring y consumidores (UI, comparacion con `rag_score_minimo`) asumen **similitud densa Qdrant**. Mezcla escalas y rompe el filtro `score >= rag_score_minimo` si se aplicara tras rerank.

### Problema 2: orden del pipeline

Hoy el pipeline es: `denso -> MMR sobre pool completo -> reranker sobre prefijo (mmr_sel[:n_toma])`. Si `top_efectivo > reranker_top_n_entrada`, candidatos densamente relevantes que MMR deja 'tarde' en su seleccion **no entran al cross-encoder**. Esto puede empeorar la calidad cuando el reranker es el filtro mas fuerte.

## Opciones de resolucion

- **Opcion A (minimo riesgo)**: mantener el orden actual y exponer dos campos en `FuenteRagDenso`: `score_denso: float` (similitud Qdrant) y `score_final: float` (score visible al consumidor). Filtro `rag_score_minimo` se aplica contra `score_denso` antes de MMR/rerank.
- **Opcion B (mas correcto teorica)**: reordenar a `denso -> reranker (sobre top-N densos, N >= k_final) -> MMR (k_final)`. Mas alineado con literatura RAG y deja la diversificacion al final.

### Recomendacion del plan

Elegir **B** si la corrida cuantitativa del golden set (TASK-71 final summary) la soporta sin regresion; **A** si rompe metricas. La decision se valida con `uv run scripts/eval_metricas_rag.py --config combinado` antes de mergear.

## Alcance

Se tocan `src/rag/recuperador_denso.py`, `FuenteRagDenso`, `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` (diagrama y tabla), y tests cualitativos en `tests/rag/test_recuperador_denso_pipeline.py`. Consumidores (UI, agente) que muestren score deben adoptar `score_final` (alias retro-compatible).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 FuenteRagDenso expone al menos score_denso: float (similitud Qdrant) y score_final: float (score visible al consumidor; igual a denso si no hubo rerank, score cross-encoder si hubo).
- [ ] #2 El filtro rag_score_minimo se aplica contra score_denso ANTES de MMR/rerank, no contra score_final.
- [ ] #3 Pipeline documentado en doc-003 con diagrama actualizado (mermaid) y tabla del orden seleccionado (A o B).
- [ ] #4 Tests cualitativos en tests/rag/test_recuperador_denso_pipeline.py: dado un fixture controlado de 5 candidatos con scores conocidos, el orden tras el pipeline coincide con el esperado para cada opcion seleccionada.
- [ ] #5 Decision A vs B documentada en Implementation Notes con evidencia cuantitativa (corrida uv run scripts/eval_metricas_rag.py --config combinado antes/despues).
- [ ] #6 Si se eligio B, no hay regresion vs baseline TASK-71 en MRR ni recall@10 (umbrales documentados).
- [ ] #7 Back-compat: campo score (alias de score_final) sigue existiendo para no romper consumidores existentes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Ejecutar baseline cuantitativa rapida: `uv run scripts/eval_metricas_rag.py --config combinado` y guardar metricas como referencia (MRR, recall@10, hit@5).
2. Decidir A o B:
   - Implementar opcion B (`denso -> reranker(top-N>=k_final) -> MMR(k_final)`) en una rama de trabajo.
   - Volver a correr `--config combinado` y comparar.
   - Si B no degrada metricas (delta MRR >= -1%, recall@10 >= -1%), adoptar B; en otro caso, A.
3. Actualizar `FuenteRagDenso` en `src/rag/recuperador_denso.py`:
   ```python
   class FuenteRagDenso(BaseModel):
       score_denso: float
       score_final: float
       score: float = Field(default=None, deprecated=True)  # alias de score_final
       # ... resto sin cambios

       @model_validator(mode='after')
       def _llenar_alias_score(self) -> 'FuenteRagDenso':
           if self.score is None:
               self.score = self.score_final
           return self
   ```
4. En `RecuperadorDenso.consultar`:
   - Aplicar `rag_score_minimo` contra `score_denso` antes de MMR/rerank.
   - Si opcion B: tras filtrar por score_minimo, mandar al reranker los top-N densos (`reranker_top_n_entrada`), luego MMR con `k_final`.
   - Si opcion A: orden actual; solo separar los campos.
5. Actualizar consumidores que leen `fuente.score`:
   - SSE / serializadores en `src/api/routers/agente.py`.
   - Frontend (mostrar `score_final` si esta disponible).
6. Actualizar `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md`:
   - Reemplazar el diagrama mermaid del pipeline.
   - Anadir tabla con `etapa | entrada | salida | filtro` mostrando el orden elegido.
7. Anadir tests cualitativos en `tests/rag/test_recuperador_denso_pipeline.py`:
   - Fixture con 5 candidatos y scores denso/cross conocidos.
   - Aserrar el orden final para cada opcion.
8. Documentar la decision A/B en Implementation Notes o Final Summary con tabla comparativa de metricas.
9. Marcar AC/DoD; `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Si se opta por A por presupuesto temporal, la tarea sigue siendo valiosa porque arregla la mezcla de escalas en `rag_score_minimo`. Si se opta por B, asegurarse de NO romper consumidores que esperaban el orden previo (revisar `src/agentes/herramientas/rag_tool.py` y la UI del chat). Asegurar serializacion JSON estable (Pydantic): `score` alias deprecado pero presente. La tool `rag_denso` (LangChain) debe mantener el schema visible al modelo; nuevos campos como `score_denso` y `score_final` opcionales en la respuesta. TASK-79 anade `batch_size` al reranker; mantener compatibilidad con esa firma.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv run pytest tests/rag/test_recuperador_denso_pipeline.py -v en verde.
- [ ] #2 uv run scripts/eval_metricas_rag.py --config combinado ejecutado y resultados anotados en Implementation Notes o Final Summary.
- [ ] #3 doc-003 actualizado con diagrama y tabla.
- [ ] #4 Tarea con status: Done sin archivar.
<!-- DOD:END -->
