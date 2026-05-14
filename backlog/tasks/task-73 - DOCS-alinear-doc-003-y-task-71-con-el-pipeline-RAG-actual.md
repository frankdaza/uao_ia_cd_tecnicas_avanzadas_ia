---
id: TASK-73
title: 'DOCS: alinear doc-003 y task-71 con el pipeline RAG actual'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-14 23:24'
updated_date: '2026-05-14 23:25'
labels:
  - rag
  - documentation
  - modulo-2
dependencies: []
references:
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
  - >-
    backlog/tasks/task-71 -
    Reranking-MMR-cross-encoder-y-tuning-hiperparametros-RAG.md
  - src/api/configuracion.py
  - src/rag/metricas_eval.py
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
  - .claude/skills/backlog-docs/SKILL.md
  - .cursor/rules/backlog-docs-format.mdc
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La auditoria de mayo 2026 sobre el pipeline RAG (recuperador denso, MMR, cross-encoder, scripts de evaluacion) identifico desalineaciones documentales entre `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md`, `backlog/tasks/task-71 - Reranking-MMR-cross-encoder-y-tuning-hiperparametros-RAG.md` y el codigo realmente instalado. Estas inconsistencias confunden a quienes implementen las TASK-74 a TASK-83 del plan, por lo que se aborda primero.

## Problemas identificados

1. **Granularidad de las metricas en doc-003**. La linea 208 de `doc-003` afirma que **toda** la suite de metricas se calcula "a nivel documento deduplicado en el top-k". En `src/rag/metricas_eval.py`:
   - `precision_at_k` y `recall_at_k` usan **archivos unicos** (deduplicado por documento).
   - `mrr` y `ndcg_at_k` usan **ranking por chunk** (no deduplicado): la posicion de cada chunk relevante cuenta de forma independiente.
2. **YAML duplicado en task-71** (lineas 138-140): el marcador `<!-- SECTION:FINAL_SUMMARY:END -->` aparece dos veces.
3. **Descripcion del problema en task-71** asume `rag_mmr_habilitado=False` como estado base "hoy", pero el default actual en `src/api/configuracion.py` es `rag_mmr_habilitado=True`. El "baseline" mencionado en la tarea corresponde al preset del script `scripts/eval_metricas_rag.py --config baseline` (que fuerza MMR/rerank off para comparacion legacy), no al default de produccion.
4. **Hot-reload de configuracion no documentado**. `obtener_configuracion()` en `src/api/configuracion.py` esta cacheada con `@lru_cache`: cambios en `.env` requieren reinicio del proceso. Los parametros RAG editados via panel admin (`PATCH /api/admin/agente-m2`) si aplican en la siguiente peticion al agente (bundle por peticion). Las TASK-77, TASK-78, TASK-79 y TASK-81 asumen este modelo y requieren que quede documentado.

## Alcance

Esta tarea **solo edita documentacion** (`doc-003` y `task-71`). No modifica codigo ni metricas. La correccion del calculo de `nDCG@k` queda en TASK-74; aqui solo se aclara la definicion teorica vigente.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 doc-003 separa explicitamente las metricas segun su granularidad: precision@k y recall@k sobre conjunto deduplicado por archivo; mrr y ndcg@k sobre ranking por chunk. Incluye una tabla con columnas: metrica | granularidad | implementacion | comentario.
- [ ] #2 task-71 queda con un unico marcador SECTION:FINAL_SUMMARY:END (lineas 138-140 actualizadas). El YAML del front matter sigue siendo valido.
- [ ] #3 La descripcion del problema en task-71 aclara la diferencia entre 'default de produccion' (rag_mmr_habilitado=True) y 'baseline del script eval_metricas_rag --config baseline' (MMR/rerank off para comparacion).
- [ ] #4 doc-003 anade un parrafo en la seccion de configuracion explicando: cambios en .env requieren reinicio (obtener_configuracion cacheada con @lru_cache); cambios via panel admin aplican en la siguiente peticion al agente.
- [ ] #5 Ambos archivos siguen las convenciones de backlog-docs-format.mdc (front matter, naming) y backlog-md (sin secretos).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer integramente `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` y `backlog/tasks/task-71 - Reranking-MMR-cross-encoder-y-tuning-hiperparametros-RAG.md` para identificar todas las menciones a metricas y defaults RAG.
2. Editar `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md`:
   - En la seccion de evaluacion sustituir el bullet de la linea 208 por una tabla `metrica | granularidad | implementacion | comentario`.
   - Anadir parrafo de hot-reload en la seccion de configuracion: `.env` -> reinicio (`@lru_cache` sobre `obtener_configuracion`); admin -> proxima peticion (bundle por peticion en `RuntimeAgenteBundle`).
3. Editar `backlog/tasks/task-71 - ...md`:
   - Eliminar el marcador `<!-- SECTION:FINAL_SUMMARY:END -->` duplicado (mantener uno).
   - Cambiar redaccion 'hoy MMR off' por 'baseline del script eval_metricas_rag --config baseline' o 'antes de TASK-71'.
4. Verificar el front matter con `uv run python -c "import yaml,sys; [yaml.safe_load(open(p).read().split('---',2)[1]) for p in sys.argv[1:]]" backlog/tasks/task-71*.md backlog/docs/doc-003*.md`.
5. Marcar AC como cumplidos via `task_edit acceptanceCriteriaCheck`.
6. Dejar `status: Done` sin archivar (regla `.cursor/rules/backlog-workflow.mdc`).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
No tocar el contenido cuantitativo del Final Summary de TASK-71; solo formato. Esta tarea NO corrige el calculo de nDCG (eso es TASK-74); solo documenta la definicion actual y deja claro que cambia TASK-74. Mantener idioma espanol latinoamericano y front matter compatible con backlog-docs-format.mdc.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 AC verificados en los archivos editados.
- [ ] #2 uv run python -c "import yaml,sys; [yaml.safe_load(open(p).read().split('---',2)[1]) for p in sys.argv[1:]]" backlog/tasks/task-71*.md backlog/docs/doc-003*.md pasa sin errores.
- [ ] #3 Tarea queda con status: Done en backlog/tasks/ (no archivar).
<!-- DOD:END -->
