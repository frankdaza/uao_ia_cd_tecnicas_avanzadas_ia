---
id: TASK-81
title: >-
  Unificar acceso a parametros RAG desde RuntimeAgenteBundle + validacion
  defensiva de config_admin_m2 en BD
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-14 23:30'
updated_date: '2026-05-14 23:30'
labels:
  - rag
  - agente-m2
  - config-admin
  - refactor
  - modulo-2
dependencies:
  - TASK-75
  - TASK-76
  - TASK-77
  - TASK-78
  - TASK-79
references:
  - src/agentes/herramientas/rag_tool.py
  - src/agentes/router.py
  - src/agentes/runtime_agente.py
  - src/api/servicios/agente_m2_config.py
  - src/api/esquemas_admin.py
  - src/api/factoria_grafo_agente.py
  - src/persistencia/modelos.py
  - src/persistencia/repositorios/config_admin_m2.py
  - alembic/versions/0005_config_admin_m2_rag_pipeline.py
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
priority: medium
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La auditoria identifico dos riesgos relacionados al consumo de parametros RAG en runtime y a la persistencia admin:

### Problema 1: doble ruta a parametros RAG en el agente

Hoy hay **dos caminos** para que el agente consuma parametros RAG:

1. La tool `rag_denso` se construye en `src/api/factoria_grafo_agente.py` y **cierra sobre `cfg = obtener_configuracion()`**: si solo se pasan `top_k`/`score_minimo` desde el bundle, los demas parametros (MMR, reranker, batch) quedan **fijos en `cfg`** y no responden a cambios admin.
2. El router (`src/agentes/router.py`, lineas 28-39 y 361-383), segun la funcion `_parametros_rag_bundle_iguales_a_configuracion(bundle, cfg)`, elige entre `tool.invoke(...)` (ruta rapida, usa la closure) o `ejecutar_rag_denso_sync(..., bundle_overrides)` (ruta lenta con override).

Si en el futuro se anade un parametro al bundle y se olvida actualizar el comparador, el agente puede ejecutar con valores **stale sin alerta**. Tras TASK-79, esto se vuelve riesgoso (nuevo `rag_reranker_batch_size`).

### Problema 2: confianza ciega en BD

`src/api/servicios/agente_m2_config.py` (lineas 113-151, metodos `*_efectivo`) lee valores persistidos sin validar rango. Valores escritos directo a BD (script de migracion, otra app, error humano) se usan tal cual y rompen el pipeline silenciosamente.

### Problema 3: limites duplicados

Los rangos validos de RAG estan duplicados entre `src/api/esquemas_admin.py` (Pydantic validators) y `src/api/servicios/agente_m2_config.py` (`aplicar_parche`, lineas 326-368). Si cambian, deben sincronizarse manualmente.

## Objetivo

- Ruta unica desde RuntimeAgenteBundle a la tool RAG: la tool NO cierra sobre `cfg`; recibe todos los parametros del bundle en cada invocacion.
- Centralizar constantes/rangos de limites RAG en un modulo unico consumido por Pydantic y el servicio admin.
- Lectura defensiva en BD: clamp + log warning si hay valores fuera de rango. Alternativa: anadir `CHECK` constraints en una nueva migracion Alembic.

## Alcance

Se tocan los archivos del agente (`herramientas/rag_tool.py`, `router.py`, `runtime_agente.py`, `factoria_grafo_agente.py`), el panel admin (`servicios/agente_m2_config.py`, `esquemas_admin.py`), opcionalmente una nueva migracion Alembic con `CHECK` constraints. Tests en `tests/agentes/`, `tests/api/admin/`, `tests/persistencia/`. No se toca el pipeline interno del recuperador (eso lo cubrieron TASK-75 a TASK-79).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 La tool rag_denso NO captura cfg por closure; recibe todos los parametros del bundle en cada invocacion (firma explicita).
- [ ] #2 Funcion _parametros_rag_bundle_iguales_a_configuracion y la bifurcacion del router se eliminan. Ruta unica: el router siempre construye argumentos desde RuntimeAgenteBundle.
- [ ] #3 Constantes de rango RAG se definen en un unico modulo (p. ej. src/api/_limites_rag.py) y son consumidas por esquemas_admin.py y servicios/agente_m2_config.py (sin duplicacion).
- [ ] #4 Lectura defensiva: Configuracion/servicio aplica clamp a valores fuera de rango leidos de BD y registra warning con contexto (campo, valor_original, valor_clamp). Tests parametrizados cubren cada parametro RAG.
- [ ] #5 Alternativa documentada en Implementation Notes: si se opta por CHECK constraints en BD, anadir migracion 0007_*.py reversible (upgrade/downgrade simetricos). Si NO, dejar la decision argumentada.
- [ ] #6 Tests de integracion: (a) PATCH /api/admin/agente-m2 con nuevo lambda -> proxima peticion POST /api/agente/stream usa nuevo lambda en el bundle; (b) PATCH con version stale -> 409 Conflict (concurrencia ya existente, conservar); (c) valor fuera de rango insertado directo a BD -> servicio recorta y registra warning.
- [ ] #7 No queda referencia a _parametros_rag_bundle_iguales_a_configuracion en el codigo del repo (grep -r vacio).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Crear `src/api/_limites_rag.py` con dataclass/dict de rangos y defaults:
   ```python
   from dataclasses import dataclass

   @dataclass(frozen=True)
   class LimiteRag:
       minimo: float | int
       maximo: float | int
       defecto: float | int

   LIMITES_RAG: dict[str, LimiteRag] = {
       'rag_top_k': LimiteRag(1, 50, 5),
       'rag_top_k_inicial': LimiteRag(1, 200, 20),
       'rag_score_minimo': LimiteRag(0.0, 1.0, 0.25),
       'rag_mmr_lambda': LimiteRag(0.0, 1.0, 0.5),
       'rag_reranker_top_n_entrada': LimiteRag(1, 50, 10),
       'rag_reranker_batch_size': LimiteRag(1, 256, 16),
   }

   def clamp(valor, campo: str) -> tuple[Any, bool]:
       limite = LIMITES_RAG[campo]
       acotado = max(limite.minimo, min(limite.maximo, valor))
       return acotado, acotado != valor
   ```
2. Refactor `src/agentes/herramientas/rag_tool.py`:
   - Eliminar la closure sobre `cfg`.
   - `crear_rag_tool(...)` recibe ahora `recuperador: RecuperadorDenso` ya construido o un `Callable` que ejecuta la consulta.
   - La tool recibe en sus argumentos (LangChain) todos los parametros RAG: `top_k`, `score_minimo`, `mmr_habilitado`, `mmr_lambda`, `reranker_habilitado`, `reranker_modelo`, `reranker_batch_size`, `reranker_top_n_entrada`.
3. Refactor `src/agentes/router.py`:
   - Eliminar `_parametros_rag_bundle_iguales_a_configuracion`.
   - En `nodo_ejecutar_tool`, siempre construir argumentos desde `RuntimeAgenteBundle.rag_*` y llamar `tool.invoke({...})`.
   - Si la tool ahora siempre recibe overrides, el comportamiento es uniforme.
4. Refactor `src/api/factoria_grafo_agente.py`:
   - Pasar `configuracion=cfg` siempre en producccion (no solo en MOCK).
   - O mejor: pasar el `recuperador` ya construido si la firma cambia.
5. Refactor `src/api/esquemas_admin.py`:
   - Usar `LIMITES_RAG` para los validadores Pydantic en `ParcheConfigAdminM2Cuerpo` y `EstadoConfigAdminM2Respuesta`.
6. Refactor `src/api/servicios/agente_m2_config.py`:
   - En `aplicar_parche`, usar `LIMITES_RAG`.
   - En metodos `*_efectivo` (lectura), aplicar `clamp` y registrar warning si recorta:
     ```python
     def _leer_rag_efectivo(self, registro) -> dict:
         resultado = {}
         for campo in LIMITES_RAG:
             valor_db = getattr(registro, campo)
             valor_clamp, hubo_clamp = clamp(valor_db, campo)
             if hubo_clamp:
                 logger.warning(...)
             resultado[campo] = valor_clamp
         return resultado
     ```
7. Decision sobre CHECK constraints: si se opta por anadirlos, migracion `0007_check_constraints_rag.py` reversible con `op.create_check_constraint(...)` y `op.drop_constraint(...)`.
8. Tests:
   - `tests/api/admin/test_patch_aplica_en_proxima_peticion.py`: httpx AsyncClient, PATCH lambda=0.3, luego POST stream, aserrar uso en el bundle.
   - `tests/api/admin/test_patch_version_stale.py`: ya existe (mantener); validar que sigue 409.
   - `tests/persistencia/test_clamp_defensivo.py`: insertar valor fuera de rango via SQL crudo, leer via servicio, aserrar clamp + warning.
9. `grep -r _parametros_rag_bundle_iguales_a_configuracion src/ tests/` vacio.
10. Marcar AC/DoD; `status: Done` sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Si `CHECK` constraints generan friccion operativa (configuracion legacy en BD), preferir clamp + alerta. La decision se argumenta en Final Summary. Mantener el contrato SSE: la herramienta sigue devolviendo el mismo schema visible al modelo. Si el refactor de `crear_rag_tool` cambia su firma, actualizar todas las llamadas (incluida `MOCK_LLM`). TASK-83 incorporara tests E2E adicionales; aqui solo los integradores de admin. Este refactor reduce significativamente la complejidad del router al eliminar la bifurcacion.
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv run pytest tests/agentes/ tests/api/admin/ tests/persistencia/ -v en verde.
- [ ] #2 uv run alembic upgrade head y downgrade -1 simetricos (si se anadio migracion).
- [ ] #3 ReadLints sobre archivos modificados sin nuevos errores.
- [ ] #4 Tarea con status: Done sin archivar.
<!-- DOD:END -->
