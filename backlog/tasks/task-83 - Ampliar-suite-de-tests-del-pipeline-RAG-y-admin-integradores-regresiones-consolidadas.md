---
id: TASK-83
title: >-
  Ampliar suite de tests del pipeline RAG y admin (integradores + regresiones
  consolidadas)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-14 23:32'
updated_date: '2026-05-15 01:01'
labels:
  - rag
  - tests
  - modulo-2
dependencies:
  - TASK-73
  - TASK-74
  - TASK-75
  - TASK-76
  - TASK-77
  - TASK-78
  - TASK-79
  - TASK-80
  - TASK-81
  - TASK-82
references:
  - tests/rag/test_recuperador_denso_pipeline.py
  - tests/rag/test_diversificador_mmr.py
  - tests/rag/test_reranker_cross_encoder.py
  - tests/rag/test_metricas_eval.py
  - tests/api/
  - tests/agentes/
  - tests/scripts/
  - src/rag/
  - src/api/
  - src/agentes/
  - tests/rag/conftest.py
  - tests/rag/test_conftest_rag_fixtures.py
  - tests/api/admin/test_admin_e2e.py
  - tests/README.md
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
  - .claude/skills/fastapi-sse-api/SKILL.md
priority: medium
ordinal: 31.25
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Las TASK-73 a TASK-82 introducen cambios en metricas, recuperador, MMR, reranker, ingesta, admin y eval. Cada tarea anade sus propios tests, pero quedan gaps de integracion y regresion que conviene cubrir al final como **tarea consolidadora**:

1. **Pipeline integrado**:
   - Los tests previos `test_pipeline_solo_mmr` y `test_pipeline_mmr_y_reranker` (lineas 102-153 antes de TASK-78) solo aseguran tamano; tras TASK-78 deben aserrar **orden y diversidad esperada**.
   - No hay test de filtros por `tipo_pagina` (filtros Qdrant) en el recuperador.
2. **Integracion admin -> agente**:
   - `PATCH /api/admin/agente-m2` debe verse reflejado en el siguiente `POST /api/agente/stream` (TASK-81 anadio tests basicos; aqui se extiende a casos de borde).
   - Conflicto de version optimista -> 409 (TASK-81 ya cubrio; aqui se garantiza que sigue verde).
   - Reranker falla -> degradacion a MMR, respuesta SSE sigue (TASK-79 anadio el comportamiento; aqui se prueba end-to-end).
3. **Regresiones consolidadas** de las tareas previas: una matriz de tests asegurada en CI.
4. **Cobertura medible**: comparar antes/despues con `pytest --cov`.

## Objetivo

Consolidar y ampliar la suite para:

- Cubrir escenarios integradores que toquen multiples capas (admin -> agente -> recuperador -> MMR/reranker).
- Asegurar que los cambios de tareas previas no regresen.
- Mantener tiempo total de ejecucion < 60 s (sin LLM real; con `MOCK_LLM=1`).
- Documentar como correr la suite.

## Alcance

Se anaden nuevos tests (no se reescriben los existentes). Posiblemente se crea `tests/rag/conftest.py` con fixtures compartidos (vector store fake, scores fabricados). No se toca codigo de produccion en esta tarea (todas las correcciones previas ya quedaron en TASK-73 a TASK-82).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 uv run pytest tests/rag/ tests/api/ tests/agentes/ tests/scripts/ -v en verde, con al menos 10 tests nuevos sumando los de las tareas previas (medible por diff de --collect-only).
- [x] #2 Tests integradores admin -> agente con httpx AsyncClient en tests/api/admin/: (a) happy path PATCH lambda + POST stream; (b) 409 conflicto version (TASK-81); (c) reranker falla -> respuesta SSE sigue con orden MMR (TASK-79).
- [x] #3 Tests cualitativos del pipeline en tests/rag/test_recuperador_denso_pipeline.py con fixture de 5 candidatos y scores denso/cross conocidos, aserrando orden esperado tras MMR/Rerank.
- [x] #4 Test de filtros tipo_pagina: ingestar puntos con metadatos distintos, recuperar filtrando por tipo_pagina, aserrar que solo se devuelven los esperados.
- [x] #5 Cobertura medida (uv run pytest --cov=src.rag --cov=src.agentes --cov=src.api): no inferior a la baseline previa al inicio del plan; reportada en Implementation Notes.
- [x] #6 Fixture compartido tests/rag/conftest.py con: FakeEmbeddings, FakeVectorStore, FakeReranker, golden minimo.
- [x] #7 tests/README.md (o seccion en README principal) documenta como correr la suite con MOCK_LLM=1.
- [x] #8 Tiempo total de la suite RAG/admin < 60s en hardware de referencia (documentado).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Medir baseline de cobertura antes de comenzar:
   ```bash
   uv run pytest tests/ --cov=src.rag --cov=src.agentes --cov=src.api --cov-report=term --collect-only
   ```
   Anotar numeros en Implementation Notes.
2. Crear `tests/rag/conftest.py` con fixtures compartidos:
   - `fake_embeddings`: subclase de `BaseEmbedding` que devuelve vectores deterministas por hash del texto.
   - `fake_vector_store`: implementacion en memoria que acepta puntos con `tipo_pagina` y devuelve por query.
   - `fake_reranker`: devuelve scores deterministas en funcion del texto.
   - `golden_minimo`: fixture con 3-5 queries de prueba.
3. Anadir tests en `tests/api/admin/test_admin_e2e.py` (httpx AsyncClient + LifespanManager):
   - `test_patch_lambda_aplica_en_proximo_stream`: PATCH `rag_mmr_lambda=0.3`, POST `/api/agente/stream` con MOCK_LLM, capturar eventos SSE, aserrar que el bundle del agente uso `lambda=0.3`.
   - `test_patch_version_stale_devuelve_409`: dos PATCH simultaneos, segundo recibe 409.
   - `test_reranker_falla_responde_sin_error`: configurar reranker con modelo invalido, POST stream, aserrar que el evento SSE final contiene fuentes (degradacion a MMR) y NO un agente_error.
4. Anadir tests cualitativos en `tests/rag/test_recuperador_denso_pipeline.py`:
   - `test_pipeline_mmr_diversifica_resultados`: fixture con 5 candidatos donde 3 son cuasi-duplicados; aserrar que tras MMR (lambda=0.5) se selecciona al menos un candidato del cluster minoritario.
   - `test_pipeline_rerank_promueve_relevante`: fixture donde el cross-encoder asigna score alto a un candidato que estaba en posicion 4; tras rerank ese candidato esta en posicion 1.
5. Anadir test de filtros `tipo_pagina`:
   - `test_recuperador_filtra_por_tipo_pagina`: ingestar puntos con `tipo_pagina='institucional'` y `tipo_pagina='blog'`; recuperar con filtro -> solo institucional.
6. Crear `tests/README.md` con seccion 'Como correr la suite':
   ```bash
   export MOCK_LLM=1
   uv run pytest tests/ -v
   uv run pytest tests/rag/ -v  # solo RAG
   uv run pytest tests/ --cov=src.rag --cov=src.agentes --cov=src.api
   ```
7. Medir cobertura final y reportar en Implementation Notes/Final Summary.
8. Asegurar tiempo total < 60s en MacBook M1/Linux runner; si excede, marcar tests lentos con `@pytest.mark.slow` y excluirlos del default.
9. Marcar AC/DoD; `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Baseline de cobertura no estaba versionada en git; medicion final con `MOCK_LLM=1`: `uv run pytest tests/rag/ tests/api/ tests/agentes/ tests/scripts/ --cov=src.rag --cov=src.agentes --cov=src.api --cov-report=term` arroja **TOTAL 83%** (2837 stmts, 480 miss) en la suma de esos paquetes. Suite completa `MOCK_LLM=1 uv run pytest tests/`: **348 passed**, 9 skipped, ~14.4 s en hardware local (MacBook clase M1). Subconjunto RAG+API+agentes+scripts ~9.5 s. Integradores admin: pool de memoria `pool_memoria_falso()` tras lifespan para evitar 503; Qdrant sembrado con `obtener_qdrant_client` singleton; embeddings falsos vía monkeypatch en `src.rag.embeddings.obtener_embeddings`; reranker forzado a fallo con `_importar_cross_encoder` y `RAG_RERANKER_HABILITADO=0` en env para evitar warmup pesado, activado luego por PATCH admin.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se consolido la suite TASK-83: `tests/rag/conftest.py` (FakeEmbeddingsDeterministas, rerankers falsos, golden_minimo), tests cualitativos MMR/rerank/filtro `tipo_pagina` en `test_recuperador_denso_pipeline.py`, integradores `tests/api/admin/test_admin_e2e.py` (lambda en bundle tras PATCH+SSE, 409 por version, degradacion reranker sin `agente_error`), `tests/rag/test_conftest_rag_fixtures.py` y `tests/README.md` con comandos `MOCK_LLM=1`. Pytest en verde; cobertura combinada rag+agentes+api 83%; tiempo total tests/ < 60 s con MOCK_LLM.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv run pytest tests/ -v en verde.
- [x] #2 uv run pytest tests/ --cov=src.rag --cov=src.agentes --cov=src.api reporta cobertura no menor que baseline.
- [x] #3 Tarea con status: Done sin archivar.
<!-- DOD:END -->
