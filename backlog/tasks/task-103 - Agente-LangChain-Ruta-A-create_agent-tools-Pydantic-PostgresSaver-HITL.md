---
id: TASK-103
title: 'Agente LangChain Ruta A: create_agent, tools Pydantic, PostgresSaver, HITL'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
updated_date: '2026-05-21 23:40'
labels:
  - modulo-3
  - taam
  - langchain
  - agente
milestone: m-0
dependencies:
  - TASK-99
  - TASK-101
references:
  - >-
    backlog/decisions/decision-7 -
    Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - proyecto-2/src/rag/vector_store.py
  - proyecto-2/src/persistencia/repositorios/vinculos_telegram.py
documentation:
  - >-
    backlog/docs/actividades/Actividad del Módulo 3_ Productización, Despliegue
    Avanzado y Sistemas Agénticos.md
modified_files:
  - proyecto-2/pyproject.toml
  - proyecto-2/uv.lock
  - proyecto-2/src/configuracion.py
  - proyecto-2/src/api/main.py
  - proyecto-2/src/agentes/
  - proyecto-2/scripts/verificar_stack_m3.sh
  - proyecto-2/tests/agentes/
  - data/structured/taam_faqs.json
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Núcleo de la rúbrica M3 (≈30 % arquitectura agente). El runtime M2 en `proyecto-1/` (LangGraph `router.py`, SSE, `PostgresChatMessageHistory`) **no** se porta. TAAM en `proyecto-2/` debe cumplir [decision-7](backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md) y UC-MVP-03.

**Prerrequisitos cerrados:** esquema OLTP y repositorios (TASK-99), RAG PDF→Qdrant (TASK-101). Este entregable es el **módulo agente** consumible por TASK-104 (`POST /chat`) y TASK-106 (webhook Telegram).

## Objetivo

Paquete `proyecto-2/src/agentes/` con agente conversacional postoperatorio: function calling estricto, memoria de hilo en Postgres (checkpointer LangChain, tablas propias), triage con HITL en escalamiento y prompt dinámico con contexto de caso + RAG.

## Contratos

| Concepto | Regla |
| --- | --- |
| `session_id` / `thread_id` | `telegram:{chat_id}` (entero Telegram) |
| Caso activo | Resolver vía `vinculos_telegram` con `vinculado_at` no nulo |
| Checkpointer | `PostgresSaver` sobre `DATABASE_URL` sync (`postgresql+psycopg://`); **no** mezclar tablas M2 ni tablas Alembic TAAM |
| FAQs | `data/structured/taam_faqs.json` (mínimo viable si TASK-114 aún no cerró el corpus) |

## Stack obligatorio (verificable)

| Pieza | Uso |
| --- | --- |
| `init_chat_model` | LLM del agente (`src/agentes/modelo.py`) |
| `create_agent` | Orquestación con tools (`src/agentes/agente_taam.py`) |
| `PostgresSaver` | Checkpointer (`src/agentes/checkpointer.py`) |
| `@dynamic_prompt` | Inyectar nombre paciente, procedimiento, notas, disclaimer (`src/agentes/prompts.py`) |
| `HumanInTheLoopMiddleware` | Interrumpir antes de `escalar_a_equipo` (severidad urgente / red flags UC-03) |

## Tools (`name` en inglés, docstrings en español, `args_schema` Pydantic)

| name | Comportamiento |
| --- | --- |
| `obtener_contexto_caso` | Metadatos del caso vinculado al `session_id` (paciente, procedimiento, notas, fecha cirugía) |
| `consultar_protocolo_rag` | Similarity en Qdrant filtrando `metadata.tipo_procedimiento_id` del caso |
| `faq_postoperatorio` | Lookup en JSON estructurado por `intent` o keywords |
| `clasificar_triage` | Salida `info` \| `seguimiento` \| `urgente` + `rationale`; si `urgente`, el prompt exige llamar `escalar_a_equipo` |
| `escalar_a_equipo` | Inserta fila en `alertas_triage` (severidad, resumen, ref. mensaje); sujeto a HITL |

## Gestión de errores (prompt + tools)

- Fallo de tool → mensaje cortés fijo al paciente; no exponer stack traces.
- RAG sin resultados → indicar consultar al equipo tratante; sugerir `escalar_a_equipo` si hay síntomas alarmantes.
- Sin vínculo Telegram → orientar a completar emparejamiento (UC-MVP-02); no inventar datos clínicos.

## Prompt base

- Disclaimer: no sustituye al médico tratante; urgencias reales → servicios de emergencia.
- Inyectar `paciente_nombre` y nombre del procedimiento cuando exista caso vinculado.

## Anti-patrones

- Router de texto libre que elige tools sin `tool_calls`.
- Reutilizar checkpointer o tablas de chat M2.
- `escalar_a_equipo` sin HITL configurado.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 `proyecto-2/scripts/verificar_stack_m3.sh` (o pytest equivalente) confirma presencia de `create_agent`, `PostgresSaver`, `HumanInTheLoopMiddleware`, `init_chat_model` y `@dynamic_prompt` bajo `proyecto-2/src/agentes/`
- [x] #2 #2 Las cinco tools listadas existen con `name` en inglés estable y `args_schema` / salida Pydantic documentada en docstrings en español
- [x] #3 #3 Test de integración (marcador `integration_postgres`): dos turnos con `thread_id=telegram:123` dejan checkpoint consultable vía `PostgresSaver` / estado del grafo
- [x] #4 #4 `HumanInTheLoopMiddleware` interrumpe en `escalar_a_equipo`; flujo documentado en `proyecto-2/src/agentes/README.md` (approve/reject para staff o demo)
- [x] #5 #5 `escalar_a_equipo` persiste fila en `alertas_triage` verificable con `RepositorioAlertasTriage` (test SQLite o Postgres)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Fase 1 — Dependencias y esqueleto
1. `uv add langchain langgraph langgraph-checkpoint-postgres` en `proyecto-2/`.
2. Crear `src/agentes/` (`modelo.py`, `checkpointer.py`, `contexto.py`, `prompts.py`, `agente_taam.py`, `servicio.py`, `tools/`).
3. Añadir `taam_faqs.json` mínimo en `data/structured/` y config opcional `AGENTE_MODELO` en `configuracion.py`.

## Fase 2 — Tools y contexto runtime
4. `ContextoTaam` (`session_id`, `session_factory`) vía `context_schema` de `create_agent`.
5. Implementar tools con acceso async a repos + Qdrant (RAG con filtro por `tipo_procedimiento_id`).
6. Tests unitarios SQLite: `obtener_contexto_caso`, `faq_postoperatorio`, `escalar_a_equipo`.

## Fase 3 — Agente, HITL y memoria
7. `construir_agente_taam(checkpointer)` con `dynamic_prompt`, `HumanInTheLoopMiddleware(interrupt_on={"escalar_a_equipo": True})`.
8. `servicio.invocar_agente` / `continuar_despues_hitl` para TASK-104.
9. Lifespan: `PostgresSaver.from_conn_string` + `setup()` en arranque (omitir en URL sqlite de tests).

## Fase 4 — Verificación rubrica
10. `scripts/verificar_stack_m3.sh` + `tests/agentes/test_stack_ruta_a.py`.
11. Test integración Postgres checkpoint (AC #3) si `EJECUTAR_INTEGRACION_POSTGRES=1`.
12. Documentar HITL en `src/agentes/README.md`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Referencias de código existente
- Repos: `src/persistencia/repositorios/` (`vinculos_telegram`, `casos_postoperatorio`, `alertas_triage`).
- RAG: `src/rag/vector_store.py`; metadata de chunks `tipo_procedimiento_id` en `src/ingesta/protocolo_pdf.py`.
- Emparejamiento: `src/api/servicios/emparejamiento.py` (formato mensaje post-vinculo).

## HITL (UC-MVP-03)
- Interrupción en tool `escalar_a_equipo`, no en `clasificar_triage` (la clasificación es lectura; el escalamiento es acción sensible).
- Respuesta `/chat` con `requiere_revision_humana: true` cuando el estado del grafo tenga `__interrupt__` (TASK-104).

## Tests sin LLM en CI
- No invocar OpenAI en tests por defecto; validar wiring, tools OLTP y script grep.
- Integración checkpoint: solo con Postgres real y `OPENAI_API_KEY` opcional para un turno mínimo.

HITL: interrupcion solo en `escalar_a_equipo`; clasificar_triage es heuristica determinista para tests sin LLM.

Integracion checkpoint: `EJECUTAR_INTEGRACION_POSTGRES=1` + OPENAI_API_KEY.

TASK-104 debe usar `servicio.invocar_agente` y mapear `requiere_revision_humana`.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado el modulo `proyecto-2/src/agentes/` con LangChain Ruta A: `init_chat_model`, `create_agent`, `PostgresSaver` (MemorySaver en SQLite/tests), `@dynamic_prompt`, `HumanInTheLoopMiddleware` en `escalar_a_equipo`, cinco tools Pydantic y servicio `invocar_agente`/`continuar_despues_hitl`. Corpus minimo `data/structured/taam_faqs.json`, script `scripts/verificar_stack_m3.sh`, README HITL y tests en `tests/agentes/` (39 tests totales pasan). Lifespan FastAPI inicializa checkpointer en Postgres.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Dependencias añadidas con `uv add` (`langchain`, `langgraph`, `langgraph-checkpoint-postgres`) y `uv.lock` actualizado
- [x] #2 `uv run pytest` en `proyecto-2/` pasa tests nuevos de `tests/agentes/` sin regresión del resto
- [x] #3 Lifespan FastAPI inicializa tablas del checkpointer (`checkpointer.setup()`) sin romper tests SQLite
- [x] #4 Sin secretos ni API keys en `backlog/tasks/`; variables solo en `.env` local
<!-- DOD:END -->
