---
id: TASK-66
title: >-
  Contexto conversacional en el compositor: historial reciente parametrizable
  desde admin y nombre de usuario siempre en el prompt
status: Done
assignee: []
created_date: '2026-05-13 00:00'
updated_date: '2026-05-13 22:15'
labels:
  - modulo-2
  - langgraph
  - memoria
  - admin
  - ux
dependencies:
  - TASK-48
  - TASK-64
  - TASK-65
references:
  - src/agentes/router.py
  - src/agentes/memoria/historial.py
  - src/agentes/runtime_agente.py
  - src/api/routers/agente.py
  - src/api/servicios/agente_m2_config.py
  - src/api/esquemas_admin.py
  - src/persistencia/modelos.py
  - frontend/src/features/admin/AdminModelPage.tsx
  - frontend/src/lib/adminApi.ts
  - frontend/src/lib/adminSchemas.ts
  - alembic/versions/0004_m2_hist_turnos_max.py
documentation:
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: high
ordinal: 900
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Contexto

En el chat M2 el usuario puede indicar su nombre o temas tratados en turnos anteriores; turnos después el asistente responde de forma genérica (“sin información”) porque el **compositor** (modelo que redacta la respuesta final) solo recibía la **pregunta actual** y el JSON de la última tool, sin el hilo conversacional persistido en PostgreSQL. El **router** sí incorporaba un resumen textual del historial para decidir la herramienta; la desalineación router/compositor explica fallos como recordar el nombre o continuar un hilo humano.

La memoria persistente y `MemoriaUsuario.cargar_ventana` ya existen (TASK-48); faltaba **inyectar** ese contexto (y el nombre de sesión) en el nodo `componer_respuesta` del grafo LangGraph.

### Objetivo

1. **Compositor con memoria efectiva**: pasar al modelo compositor los mensajes previos ya acotados por la ventana (misma semántica de “turno” que `aplicar_tope_turnos_ultimos`: cada `HumanMessage` cuenta como ancla de turno), como texto estructurado en el system prompt (o equivalente claro), sin duplicar el turno actual (este sigue en el `HumanMessage` final con `state["pregunta"]`).

2. **Nombre de usuario siempre visible al compositor**: añadir un bloque de sistema fijo con el `nombre` del `Usuario` autenticado (`state["usuario"]`, ya inyectado desde `POST /api/agente/stream`) cuando no esté vacío, para identificación de sesión **sin** exigir que el modelo infiera el nombre solo desde mensajes pasados. Nota de producto: si el usuario prefiere un apodo distinto al registrado al iniciar sesión, ese dato solo aparecerá cuando conste en el historial persistido.

3. **Parámetro administrable**: exponer un entero **efectivo** `historial_turnos_max` (límites alineados a `HISTORIAL_TURNOS_MAX` en `.env`: 1–200) en `GET/PATCH /api/admin/config`, persistido en columna nullable de `config_admin_m2` (NULL = usar valor de entorno). El siguiente `POST /api/agente/stream` debe usar el snapshot sin reiniciar Uvicorn.

4. **Estrategia MVP**: ventana deslizante de turnos (sin resumen LLM adicional). Documentar en notas que un resumen rolling sería evolución futura si el contexto supera presupuestos de tokens.

### Fuera de alcance (sugerido)

- Exponer `HISTORIAL_DIAS_MAX` en admin (puede ser tarea aparte).
- Resumen automático del hilo con segundo LLM.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [x] #1 El compositor recibe en su contexto (system o mensajes) el historial de turnos previos cargado con el mismo tope efectivo que usa `cargar_ventana(turnos_max=...)`.
- [x] #2 Si `usuario.nombre` no está vacío, el compositor recibe siempre un bloque explícito con ese nombre (datos de sesión autenticada).
- [x] #3 `GET /api/admin/config` devuelve `historial_turnos_max` efectivo (PostgreSQL si columna no nula; si no, valor desde `HISTORIAL_TURNOS_MAX` / configuración).
- [x] #4 `PATCH /api/admin/config` acepta `historial_turnos_max` entero en rango válido, persiste y la respuesta refleja el nuevo valor efectivo; control optimista de `version` sin regresión.
- [x] #5 Panel admin (“Modelo” o sección acordada): campo numérico para editar y guardar `historial_turnos_max` con validación cliente coherente con el API.
- [x] #6 Pruebas automatizadas (pytest y vitest según archivos tocados) que cubren al menos: respuesta GET con campo nuevo; PATCH; y que el compositor reciba historial+nombre en un escenario de grafo con dobles (sin OpenAI real).
- [x] #7 `uv run pytest` y `ruff check` verdes; frontend `pnpm --dir frontend exec eslint` / build según scripts del repo sin errores nuevos en archivos tocados.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Migración Alembic: columna `historial_turnos_max` (Integer, nullable) en `config_admin_m2` con `down_revision` apuntando a la última revisión del repo.
2. ORM `ConfigAdminM2` + `ServicioAgenteM2Config`: método `historial_turnos_max_efectivo`, fusión en `construir_bundle_tiempo_ejecucion`, soporte en `aplicar_parche` con validación 1–200.
3. `RuntimeAgenteBundle`: nuevo campo; `router.py`: `nodo_cargar_memoria` pasa `turnos_max` desde el bundle; `nodo_componer_respuesta` añade bloques de nombre e historial; `_historial_a_texto_router` admite usar la lista completa cargada (`max_bloques` opcional).
4. `esquemas_admin.py` + `admin.py` (`_construir_estado_config_respuesta`).
5. Frontend: `adminSchemas.ts`, `adminFormValidators.ts`, `AdminModelPage.tsx`, tests de schema/validador.
6. Tests pytest: ampliar `test_admin_router.py`; añadir o extender prueba del grafo que capture mensajes enviados al compositor.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **Ventana vs resumen**: la ventana de turnos es el estándar de la industria para MVPs de chat con memoria; evita latencia y coste de un segundo LLM y reduce riesgo de alucinación en resúmenes. Si más adelante el prompt supera el contexto del modelo, valorar truncado por tokens o resumen asíncrono bajo umbral.
- **Coordinación Alembic**: si en el árbol ya existe `0003_config_admin_m2_rag.py`, la nueva migración debe encadenarse como `0004_...` revisando `0003`.
- **Privacidad**: el historial inyectado es el mismo ya persistido para la sesión; no ampliar la retención más allá de lo que ya define `HISTORIAL_DIAS_MAX` + tope de turnos.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [x] #1 Criterios de aceptación verificados y marcados al cierre de la implementación.
- [x] #2 Revisión rápida de que no se exponen secretos ni PII extra en logs o respuestas admin.
- [x] #3 Rama lista para integración: tests y lint verdes según criterios anteriores.
<!-- DOD:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementada columna `historial_turnos_max` en `config_admin_m2` (Alembic 0004), fusion en `ServicioAgenteM2Config` y `RuntimeAgenteBundle`. El grafo pasa `turnos_max` al cargar memoria y el compositor incluye nombre de sesion e historial textual en el system prompt. Panel admin con campo validado; tests pytest (`test_compositor_recibe_nombre_registrado_e_historial_en_system`, admin GET/PATCH) y vitest en schemas/validators. Ejecutar `alembic upgrade head` en entornos con base de datos.
<!-- SECTION:FINAL_SUMMARY:END -->
