---
id: TASK-56
title: >-
  Router Agent con LangGraph (StateGraph) y nodos de memoria, tools y
  composición
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-15 01:01'
labels:
  - langgraph
  - agente
  - modulo-2
dependencies:
  - TASK-48
  - TASK-51
  - TASK-54
  - TASK-55
references:
  - src/agentes/estado.py
  - src/agentes/router.py
  - src/qa/prompt.py
documentation:
  - 'https://langchain-ai.github.io/langgraph/'
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
modified_files:
  - src/agentes/estado.py
  - src/agentes/router.py
  - src/qa/prompt.py
  - src/qa/__init__.py
  - tests/agentes/test_router_grafo.py
priority: high
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El núcleo agéntico orquesta: carga de memoria, decisión de tool con LLM + tool binding, ejecución de `FaqStructuredTool` o `RagTool`, composición de respuesta final con prompt institucional Lili, y persistencia del turno.

## Objetivo

1. **`src/agentes/estado.py`**: `TypedDict` o dataclass `EstadoAgente` con campos mínimos:
   - `pregunta`, `mensajes_historial`, `tool_decidida`, `resultado_tool`, `respuesta_final`, `fuentes`, `pensamientos`, `usuario`, `session_id`, flags como `primer_turno`.

2. **`src/agentes/router.py`**: implementar grafo **LangGraph** (`StateGraph`) con nodos:
   - `cargar_memoria`
   - `decidir_tool` — LLM con **tool binding** sobre `[FaqStructuredTool, RagTool]` y system prompt desde meta-prompt JSON
   - `ejecutar_tool` — rama condicional según tool elegida
   - `componer_respuesta` — LLM con system prompt institucional (`src/qa/prompt.py` como base) + contexto de tool + memoria
   - `persistir_turno` — escribe mensajes humano/AI vía `MemoriaUsuario`

3. Exponer `crear_grafo_agente(...) -> CompiledGraph` (nombre exacto en español ASCII) configurable con dependencias inyectadas (LLM, tools, memoria).

4. **Streaming**: soportar `astream_events` (o API equivalente estable) para token-a-token hacia la capa SSE (task-57).

5. **Saludo inicial**: si `primer_turno=True` y hay nombre de usuario, usar `saludo_template` del meta-prompt; si hay historial previo cargado, comportamiento documentado (re-saludo suave vs silencio).

## Tests

Usar **`FakeListChatModel`** de LangChain para secuencias deterministas de tool_calls y texto; no llamar OpenAI en unit tests.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Grafo compila y ejecuta un turno completo en test con LLM fake
- [x] #2 Rama FAQ vs RAG seleccionable por fixtures de `FakeListChatModel`
- [x] #3 Estado incluye `fuentes` cuando la tool RAG devuelve metadata
- [x] #4 `pensamientos` captura decisión del router (tool + razón breve) para SSE
- [x] #5 `persistir_turno` llama a memoria (verificado con mock/fake history)
- [x] #6 `astream_events` expone eventos consumibles por capa HTTP (smoke test)
- [x] #7 Sin imports de BM25 ni `src/retrieval/recuperador.py`
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Definir estado y reducers LangGraph para listas (mensajes, pensamientos).
2. Implementar nodos como funciones puras donde sea posible; inyectar clientes.
3. Cablear edges condicionales post `decidir_tool`.
4. Implementar nodo compositor reutilizando políticas de `prompt.py`.
5. Tests con grafo y fake model.
6. Preparar interfaz para cancelación (task-57).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Mantener trazabilidad: guardar en estado el nombre de tool y argumentos serializables (sin volcar corpus completo).
- Revisar límites de tokens al inyectar memoria + contexto RAG.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agregaron `src/agentes/estado.py` (TypedDict `EstadoAgente` con reducer en `pensamientos`) y `src/agentes/router.py` con `crear_grafo_agente` que compila un StateGraph lineal: cargar_memoria, decidir_tool (bind_tools + meta-prompt), ejecutar_tool (FAQ vs RAG), componer_respuesta (prompt Lili + resultado de tool + saludo segun `primer_turno` e historial), persistir_turno. Las tools por defecto se importan de forma diferida dentro de `crear_grafo_agente` para no cargar Qdrant al importar el router. Se ajustó `src/qa/__init__.py` con `__getattr__` para no cargar BM25 al importar submodulos como `prompt`, y `prompt.py` difiere la importación de `DocumentoRecuperado` a las funciones que la usan. Tests en `tests/agentes/test_router_grafo.py` con `FakeListChatModel` (compositor) y doble `_ListaRouterFalso` para tool_calls; smoke de `astream_events`. `uv run pytest` y `ruff check` en archivos tocados verdes.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest tests/agentes/` verde para tests del router
- [x] #2 `ruff check` sin errores nuevos
- [x] #3 Ejemplo de invocación síncrona documentado para depuración local
<!-- DOD:END -->
