---
id: TASK-103
title: 'Agente LangChain Ruta A: create_agent, tools Pydantic, PostgresSaver, HITL'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
labels:
  - modulo-3
  - taam
  - langchain
  - agente
milestone: m-0
dependencies:
  - TASK-99
  - TASK-101
documentation:
  - >-
    backlog/docs/actividades/Actividad del Módulo 3_ Productización, Despliegue
    Avanzado y Sistemas Agénticos.md
priority: high
ordinal: 2070
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Núcleo de la rúbrica M3 (30% arquitectura agente). **No** reutilizar el StateGraph de `proyecto-1/src/agentes/router.py` como solución final; implementar stack del curso.

## Objetivo

Módulo `proyecto-2/src/agentes/` con agente conversacional postoperatorio y tools estrictas.

## Componentes obligatorios (verificables en repo)

- `init_chat_model` para LLM.
- `create_agent` para orquestación.
- `PostgresSaver` como checkpointer (`thread_id` = session_id).
- `HumanInTheLoopMiddleware` en severidad **urgente** o red flags del UC-03.
- `dynamic_prompt` para inyectar contexto RAG + notas del caso.

## Tools (name en inglés, docstrings español)

| name | Función |
|------|--------|
| `consultar_protocolo_rag` | Retrieval filtrado por tipo_procedimiento_id del caso |
| `faq_postoperatorio` | JSON fijo `data/structured/taam_faqs.json` |
| `clasificar_triage` | Output Pydantic: severidad info/seguimiento/urgente + rationale |
| `escalar_a_equipo` | Inserta `alertas_triage` |
| `obtener_contexto_caso` | Lee notas y metadatos del caso por session |

## Gestión de errores

- Tool falla → respuesta cortés al paciente (texto fijo en prompt).
- RAG vacío → escalar o mensaje "consulte a su equipo".

## Prompt

- Disclaimer: no reemplaza médico tratante; urgencias → servicios de emergencia.
- Inyectar nombre paciente y tipo procedimiento si hay caso vinculado.

## Fallas a evitar

- Router de texto libre sin tool_calls.
- Mezclar checkpointer M2 con TAAM en misma tabla sin prefijo.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Grep/CI confirma uso de create_agent, PostgresSaver, HumanInTheLoopMiddleware, init_chat_model
- [ ] #2 Cada tool tiene schema Pydantic y name estable en inglés
- [ ] #3 Invocación de prueba con thread_id telegram:123 persiste turnos en Postgres
- [ ] #4 clasificar_triage urgente dispara flujo HITL documentado
- [ ] #5 escalar_a_equipo crea fila alertas_triage consultable por API staff
<!-- AC:END -->
