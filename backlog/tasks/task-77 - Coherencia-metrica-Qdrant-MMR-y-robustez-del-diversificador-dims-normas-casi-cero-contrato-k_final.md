---
id: TASK-77
title: >-
  Coherencia metrica Qdrant/MMR y robustez del diversificador (dims, normas casi
  cero, contrato k_final)
status: In Progress
assignee:
  - Frank Daza
created_date: '2026-05-14 23:27'
updated_date: '2026-05-15 00:01'
labels:
  - rag
  - mmr
  - qdrant
  - correctness
  - modulo-2
dependencies:
  - TASK-73
  - TASK-76
references:
  - src/api/configuracion.py
  - src/rag/diversificador_mmr.py
  - src/rag/qdrant_store.py
  - scripts/indexar_corpus_qdrant.py
  - tests/rag/test_diversificador_mmr.py
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La auditoria detecto que el algoritmo MMR en `src/rag/diversificador_mmr.py` asume coseno entre vectores: `mmr = lambda * sim(q, d) - (1 - lambda) * max_s sim(d, s)`. Sin embargo, hay puntos de incoherencia con el resto del pipeline:

1. **Metrica Qdrant variable**. `src/api/configuracion.py` (lineas 66-72) admite `qdrant_distance` en `{Cosine, Dot, Euclid, Manhattan}`. Con vectores **no normalizados** y metrica distinta a `Cosine`, el orden por score Qdrant no coincide con el `rel` que usa MMR -> diversificacion incoherente entre las dos etapas.
2. **Sin validacion de dimensiones**. `diversificador_mmr.py` (lineas 66-74) no valida que `len(embedding_consulta) == len(vector_chunk)`. Si se mezclan modelos de embedding distintos en la coleccion, falla con error opaco de NumPy.
3. **Normas casi cero**. Si `norma(vector) < EPS_NORM` (lineas 28-32), el vector **no** se normaliza: la similitud coseno deja de comportarse como esperamos. Hoy se cuela como dato corrupto silencioso.
4. **Contrato k_final**. Si `k_final > len(pool)`, hoy se trunca a `len(pool)` sin advertencia. Conviene documentar.

## Objetivo

- Validar al arranque (o primer uso) que `qdrant_distance == Cosine` cuando `rag_mmr_habilitado=True`.
- Asegurar que la ingesta produce vectores **normalizados** (norma 1).
- Validar dimensiones y manejar normas casi cero en `diversificador_mmr.py`.
- Documentar el contrato `k_final > pool` en docstring.

## Alcance

Se tocan `src/rag/diversificador_mmr.py`, `src/rag/qdrant_store.py` (validacion en `asegurar_coleccion`), `scripts/indexar_corpus_qdrant.py` (normalizacion en ingesta) y tests en `tests/rag/test_diversificador_mmr.py`. La opcion alternativa de implementar MMR generico para cualquier metrica de Qdrant queda fuera del alcance (mas invasivo); se documenta la decision en doc-003.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 asegurar_coleccion en src/rag/qdrant_store.py valida la combinacion metrica + flag MMR: si qdrant_distance != Cosine y rag_mmr_habilitado=True, levanta ValueError con mensaje claro al iniciar la app o al primer uso de la coleccion.
- [ ] #2 scripts/indexar_corpus_qdrant.py normaliza vectores antes del upsert (norma 1) o documenta que el embedder ya lo hace (assert al inicio si no se cumple). Verificable consultando un punto via qdrant-client y midiendo la norma.
- [ ] #3 diversificador_mmr.py valida len(embedding_consulta) == len(vector_chunk) al inicio del bucle y levanta ValueError('mmr_dim_mismatch') con mensaje claro.
- [ ] #4 Vectores con norma < EPS_NORM se descartan del candidato con log warning; no rompen MMR.
- [ ] #5 Tests nuevos en tests/rag/test_diversificador_mmr.py: (a) pool con 1 solo candidato y k_final=3 -> devuelve 1; (b) dimensiones mismatch -> ValueError; (c) vector de norma casi cero -> omitido del resultado; (d) lambda extremos 0.0 y 1.0 confirman extremos puros (refuerzo).
- [ ] #6 Docstring de aplicar_mmr explica el contrato cuando k_final > len(pool).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Modificar `src/rag/diversificador_mmr.py`:
   - Anadir validacion al inicio del bucle: `if len(emb_q) != len(vec): raise ValueError(f'mmr_dim_mismatch: query={len(emb_q)} vs vector={len(vec)}')`.
   - Cambiar el manejo de norma casi cero: si `norma < EPS_NORM`, descartar el candidato del pool con `logger.warning(...)` antes del bucle.
   - Ampliar docstring de `aplicar_mmr`: explicar contrato `k_final > pool` (se trunca a `len(pool)` con log informativo).
2. Modificar `src/rag/qdrant_store.py`:
   - En `asegurar_coleccion`, despues de crear/abrir la coleccion, validar: si `cfg.rag_mmr_habilitado and cfg.qdrant_distance != 'Cosine'`, levantar `ValueError('mmr_requires_cosine: configura QDRANT_DISTANCE=Cosine o desactiva RAG_MMR_HABILITADO')`.
3. Modificar `scripts/indexar_corpus_qdrant.py`:
   - Anadir helper `_normalizar_l2(vec: list[float]) -> list[float]` y aplicarlo a cada vector antes del upsert (o usar `numpy.linalg.norm` con `axis=1`).
   - Si el embedder ya devuelve vectores normalizados (OpenAI text-embedding-3-*), documentar y mantener la normalizacion como defensiva (idempotente).
4. Anadir tests en `tests/rag/test_diversificador_mmr.py`:
   - `test_aplicar_mmr_pool_unico_con_k_mayor` -> input 1 candidato, k_final=3 -> devuelve 1.
   - `test_aplicar_mmr_dim_mismatch_levanta` -> emb_q de 4 dims, candidatos de 3 dims -> `ValueError`.
   - `test_aplicar_mmr_norma_casi_cero_omite_candidato` -> vector con norma 1e-12 omitido; los demas se seleccionan.
   - Reforzar `test_aplicar_mmr_lambda_extremos` con aserciones especificas sobre el orden.
5. Actualizar `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md`: nota sobre 'MMR requires Cosine'.
6. Verificar normalizacion via shell ad hoc tras ingesta (puede ser un test integracion separado).
7. Marcar AC/DoD; `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
OpenAI `text-embedding-3-small/large` ya devuelve vectores normalizados; modelos HuggingFace locales no siempre. La normalizacion en `indexar_corpus_qdrant.py` es idempotente y segura. Si el equipo prefiere mantener flexibilidad de metrica, alternativa: implementar MMR generico usando la misma metrica que Qdrant (mas invasivo y fuera de alcance aqui). Documentar la decision elegida en doc-003. Mantener EPS_NORM como constante del modulo para que tests puedan importarla. TASK-83 anadira tests de integracion adicionales que cubren ingesta + recuperacion.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv run pytest tests/rag/test_diversificador_mmr.py -v en verde.
- [ ] #2 Ingesta end-to-end con uv run scripts/indexar_corpus_qdrant.py produce vectores normalizados (verificable con qdrant-client).
- [ ] #3 Tarea con status: Done sin archivar.
<!-- DOD:END -->
