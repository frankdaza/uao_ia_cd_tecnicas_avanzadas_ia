---
id: TASK-79
title: Cross-encoder con batch_size configurable y warmup en lifespan FastAPI
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-14 23:28'
updated_date: '2026-05-15 01:01'
labels:
  - rag
  - reranker
  - performance
  - modulo-2
dependencies:
  - TASK-78
references:
  - src/rag/reranker_cross_encoder.py
  - src/api/configuracion.py
  - src/api/esquemas_admin.py
  - src/api/servicios/agente_m2_config.py
  - src/api/main.py
  - src/persistencia/modelos.py
  - tests/api/test_lifespan.py
  - alembic/versions/0006_config_admin_m2_reranker_batch_size.py
  - frontend/src/lib/adminSchemas.ts
  - frontend/src/features/admin/AdminModelPage.tsx
  - frontend/src/lib/adminFormValidators.ts
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
  - .claude/skills/fastapi-sse-api/SKILL.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La auditoria detecto tres oportunidades en el reranker cross-encoder (`src/rag/reranker_cross_encoder.py`):

1. **Falta batch_size**. `CrossEncoder.predict` se llama sobre **todos** los pares (query, candidato) sin `batch_size` explicito (lineas 53-70). Con `rag_reranker_top_n_entrada` alto y modelos grandes (BGE), picos de VRAM/RAM y latencia altos.
2. **Cold start**. La **primera peticion** con reranker activo carga el modelo desde disco o HF Hub (lineas 39-50). Latencia visible en SSE para el primer usuario tras el arranque.
3. **Errores opacos en predict**. Items no convertibles a `float` se sustituyen por `0.0` (lineas 65-69) y empatan candidatos de forma silenciosa, dificultando diagnostico.

## Objetivo

- Anadir setting `rag_reranker_batch_size` (default 16, rango [1, 256]) en `Configuracion` y panel admin (Pydantic + servicio + migracion Alembic incremental si requiere columna BD).
- Pasar `batch_size=cfg.rag_reranker_batch_size` a `CrossEncoder.predict`.
- Anadir hook de **warmup** opcional en `lifespan` de FastAPI: si `rag_reranker_habilitado=True`, ejecutar `puntuar('warmup', ['warmup'])` y registrar latencia en log; ignorar fallos para no bloquear el arranque.
- Manejar items no convertibles a float con politica documentada (descartar candidato con log, no contaminar el orden con 0.0).

## Alcance

Se tocan `src/rag/reranker_cross_encoder.py`, `src/api/configuracion.py`, `src/api/esquemas_admin.py`, `src/api/servicios/agente_m2_config.py`, `src/api/main.py` (lifespan), opcionalmente `src/persistencia/modelos.py` + nueva migracion Alembic (`0006_*.py`). Tests en `tests/rag/test_reranker_cross_encoder.py` y `tests/api/test_admin.py`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Nuevo setting rag_reranker_batch_size: int en src/api/configuracion.py (default 16, rango [1, 256]) con docstring y validador Pydantic.
- [x] #2 Setting expuesto en panel admin (Pydantic en esquemas_admin.py + servicio en agente_m2_config.py); si requiere persistencia, migracion Alembic 0006_*.py con columna nueva y downgrade reversible.
- [x] #3 src/rag/reranker_cross_encoder.py.puntuar(...) pasa batch_size=cfg.rag_reranker_batch_size a CrossEncoder.predict.
- [x] #4 Hook de warmup opcional en lifespan de src/api/main.py: si rag_reranker_habilitado=True, ejecuta puntuar('warmup', ['warmup']) ignorando errores y registra latencia.
- [x] #5 Items no convertibles a float en predict se descartan del candidato con log warning (no se sustituyen por 0.0 que contamine el orden).
- [x] #6 Tests en tests/rag/test_reranker_cross_encoder.py: (a) tamano de lote respetado (mock predict que registra batches); (b) salida con cardinalidad distinta no rompe el caller; (c) item NaN/None descartado con log.
- [x] #7 Lifespan FastAPI no bloquea > 5s en el warmup; si HF Hub esta caido, log y continua.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Anadir `rag_reranker_batch_size: int = 16` en `src/api/configuracion.py` (Pydantic Field con rango [1, 256], docstring).
2. Si el flag debe persistirse via admin, anadir:
   - Columna `rag_reranker_batch_size INTEGER NOT NULL DEFAULT 16` en `src/persistencia/modelos.py` (tabla `config_admin_m2`).
   - Migracion Alembic `0006_config_admin_m2_reranker_batch.py` con upgrade y downgrade simetricos.
   - Schema Pydantic en `src/api/esquemas_admin.py` (validacion rango).
   - Servicio `src/api/servicios/agente_m2_config.py` (clamp en lectura si la TASK-81 ya esta o sera).
3. Modificar `src/rag/reranker_cross_encoder.py`:
   - `puntuar(self, consulta: str, candidatos: list[str], batch_size: int | None = None) -> list[float]`.
   - Pasar `batch_size=batch_size or self._batch_size_default` a `CrossEncoder.predict`.
   - Politica de errores: si `float(x)` falla, descartar el candidato y registrar warning con indice; conservar resto.
4. Modificar `src/rag/recuperador_denso.py` para pasar `cfg.rag_reranker_batch_size` al reranker.
5. En `src/api/main.py` lifespan:
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       cfg = obtener_configuracion()
       if cfg.rag_reranker_habilitado:
           try:
               await asyncio.to_thread(_warmup_reranker, cfg)
           except Exception:
               logger.exception('reranker.warmup_fallo')
       yield
   ```
   Helper `_warmup_reranker(cfg)` carga el reranker e invoca `puntuar('warmup', ['warmup'])` registrando latencia.
6. Tests:
   - Mock `CrossEncoder.predict` que registra los `batch_size` recibidos.
   - Test que devuelve cardinalidad distinta -> no rompe el caller (politica de descarte).
   - Test que devuelve `[0.5, float('nan'), 0.7]` -> el candidato NaN se descarta.
   - Test del lifespan en `tests/api/test_lifespan.py` con HF Hub mockeado para latencia baja.
7. Actualizar doc-003: bullet en seccion reranker con batch_size y warmup.
8. `uv run alembic upgrade head` y `downgrade -1`.
9. Marcar AC/DoD; `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Evitar que el warmup bloquee el arranque > 5s; si HF Hub esta caido, log y continuar (no fallar el arranque). Para CPU-only, batch 8-16 suele ser optimo; documentar en doc-003 con tabla `cpu | gpu | batch sugerido`. La migracion Alembic puede ser numero `0006` o posterior segun el estado al implementar. La TASK-81 anadira clamp defensivo en lectura para este y otros parametros. Si se opta por NO persistir el batch_size en BD (solo settings .env), la tarea es mas corta; aclarar en Implementation Notes la decision.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado rag_reranker_batch_size (env RAG_RERANKER_BATCH_SIZE, default 16, rango 1-256) en Configuracion; columna admin + migracion Alembic 0006; panel admin y ServicioAgenteM2Config (efectivo + PATCH). RerankerCrossEncoder.puntuar usa batch_size en predict, devuelve list[float|None] descartando no finitos con warning. RecuperadorDenso pasa batch_size y filtra None. RuntimeAgenteBundle y router/rag_tool alineados. Lifespan FastAPI: warmup opcional con asyncio.wait_for 5s, errores/timeout solo log. Tests: test_reranker_cross_encoder, test_admin_router, test_lifespan (TestClient), mocks pipeline con **kwargs. doc-003 actualizado. Alembic upgrade/downgrade no ejecutado aqui (PostgreSQL no disponible en el entorno); validar en CI o local con DB.

Panel React admin: schema Zod, validador y campo rag_reranker_batch_size en AdminModelPage.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv run pytest tests/rag/test_reranker_cross_encoder.py tests/api/test_admin.py -v en verde.
- [ ] #2 uv run alembic upgrade head y downgrade -1 simetricos (si se anadio migracion).
- [x] #3 doc-003 documenta el nuevo flag y el warmup.
- [x] #4 Tarea con status: Done sin archivar.
<!-- DOD:END -->
