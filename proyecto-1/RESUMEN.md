# Resumen del grafo del agente (Modulo 2)

Documento breve para enlaces desde el [README](README.md). La guia operativa completa esta en [doc-003 — Arquitectura operativa del agente](backlog/docs/doc-003%20-%20Arquitectura-Agente-Modulo-2.md) y las decisiones de stack en [decision-3](backlog/decisions/decision-3%20-%20Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md).

## Orden de nodos (LangGraph)

1. **`cargar_memoria`**: lee la ventana de historial desde PostgreSQL (`PostgresChatMessageHistory`) acotada por dias y turnos maximos efectivos (bundle + admin).
2. **`inferir_intencion`**: clasifica `factual` / `listado` / `conteo` con heuristica de texto (sin LLM).
3. **`decidir_tool`**: si la intencion es listado/conteo y hay filtros deducibles, fabrica un `tool_call` sintetico a `listar_estructurado`; si no, invoca el **LLM router** con tool-calling (`bind_tools` + `ainvoke` en runtime async).
4. **`ejecutar_tool`**: ejecuta la `StructuredTool` elegida (`faq_estructurada`, `rag_denso`, `listar_estructurado`). Si `listar_estructurado` devuelve `conteo == 0`, hay **fallback** a `rag_denso` con la pregunta original.
5. **`componer_respuesta`**: el **LLM compositor** arma la respuesta final con el contexto de herramienta serializado en el system prompt.
6. **`persistir_turno`**: guarda humano + AI en memoria Postgres con metadata (tool y fuentes RAG).

## Herramientas (`name` en ingles)

| Tool | Rol |
| --- | --- |
| `faq_estructurada` | Respuestas deterministas desde `data/structured/faqs.json`. |
| `rag_denso` | Recuperacion densa sobre Qdrant (LlamaIndex); sin BM25 en runtime M2. |
| `listar_estructurado` | Scroll + filtros de payload en Qdrant para listados/conteos; requiere filtros validos o usa scroll acotado sin filtro (ver codigo). |

## SSE hacia el frontend

`POST /api/agente/stream` emite eventos JSON: `pensamiento`, `herramienta`, `token`, `fuentes`, `final`, `error`. Ver doc-002/doc-003 para el contrato detallado.
