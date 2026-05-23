---
id: TASK-84
title: >-
  LangSmith: trazas opcionales LangGraph/LangChain, variables de entorno y
  metadatos de correlacion
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-15 12:00'
updated_date: '2026-05-16 01:59'
labels:
  - langsmith
  - observabilidad
  - modulo-2
  - langgraph
dependencies:
  - TASK-56
  - TASK-57
references:
  - src/api/main.py
  - src/api/configuracion.py
  - src/api/tracing_langchain.py
  - src/api/routers/agente.py
  - src/agentes/router.py
  - .env.example
  - backlog/decisions/decision-5 - LangSmith-Observabilidad-y-Evaluacion-M2.md
documentation:
  - 'https://docs.langchain.com/langsmith/home'
  - backlog/decisions/decision-5 - LangSmith-Observabilidad-y-Evaluacion-M2.md
priority: medium
ordinal: 15.625
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El agente M2 combina **LangGraph** (router), **LangChain** (LLM con tools, memoria Postgres) y **LlamaIndex + Qdrant** (RAG), expuesto por **FastAPI** y streaming **SSE**. Sin observabilidad centralizada, depurar routing, latencias y calidad de recuperacion depende sobre todo de logs locales.

**LangSmith** es la plataforma del ecosistema LangChain para trazas, evaluacion y analisis de costes. El ADR [decision-5](../decisions/decision-5%20-%20LangSmith-Observabilidad-y-Evaluacion-M2.md) define postura **opcional por entorno**, variables tipicas (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`, `LANGCHAIN_ENDPOINT`), riesgos de PII y fases de adopcion (documentacion, trazas dev/staging, metadatos, evaluacion).

Hoy el repositorio **no** aplica ni documenta en codigo de forma unificada el arranque de tracing compatible con LangChain/LangGraph.

## Objetivo

1. **Documentacion de entorno**: ampliar `.env.example` con placeholders (sin valores reales) para las variables de tracing alineadas al ADR.
2. **Configuracion Pydantic**: extender `Configuracion` en `src/api/configuracion.py` con campos opcionales mapeados a `LANGCHAIN_*` (identificadores de modelo en espanol ASCII; alias de entorno en ingles estable por contrato LangChain).
3. **Helper DRY**: un modulo dedicado `src/api/tracing_langchain.py` con `aplicar_tracing_langchain_desde_config(cfg)` que, solo cuando el equipo activa trazas y hay clave API, escribe en `os.environ` los valores que el SDK de LangChain/LangGraph lee en tiempo de ejecucion (el cargador de `.env` via Pydantic no garantiza que otras librerias vean esas claves si solo existen en el modelo).
4. **Lifespan**: invocar el helper al inicio de `lifespan` en `src/api/main.py`, **antes** de `construir_grafo_agente_produccion_o_none(cfg)`.
5. **Metadatos de correlacion (fase 2 ligera)**: en `POST /api/agente/stream`, pasar `metadata` en el `config` de `astream_events` con identificadores **no sensibles** (p. ej. UUID interno de usuario como texto); **no** incluir `documento_identidad`, nombre libre ni texto de la pregunta en metadatos.
6. **Pruebas**: tests unitarios del helper sin red (sin enviar trazas reales); restaurar o aislar `os.environ` entre casos.
7. **Fuera de alcance (YAGNI)**: datasets LangSmith, experimentos de evaluacion batch y despliegue self-hosted completo quedan para tareas futuras salvo decision explicita.

## Privacidad y cumplimiento

- Revisar politicas institucionales antes de activar trazas con datos reales de usuarios o corpus sensible (ver Trust Center de LangChain en el ADR).
- Separar proyectos LangSmith por entorno (`LANGCHAIN_PROJECT`).
- El export de trazas debe ser **no bloqueante** para el chat; no introducir retries custom que retrasen la respuesta (confiar en el comportamiento tolerante a fallos del SDK).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `.env.example` documenta `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` y `LANGCHAIN_ENDPOINT` (opcional) con comentarios en español latinoamericano; sin secretos reales.
- [x] #2 `Configuracion` expone campos opcionales con `validation_alias` hacia esas variables de entorno (nombres de atributo en espanol ASCII).
- [x] #3 `aplicar_tracing_langchain_desde_config` en `src/api/tracing_langchain.py` centraliza la escritura a `os.environ`; si trazas desactivadas o sin clave API, no fuerza activacion y registra advertencia clara cuando se solicita sin clave.
- [x] #4 `lifespan` en `src/api/main.py` llama al helper antes de construir el grafo del agente.
- [x] #5 `astream_events` recibe `metadata` con al menos el identificador interno de usuario (UUID) sin campos de PII textual (doc_id, nombre).
- [x] #6 Tests en `tests/api/` verifican el helper (habilitado / deshabilitado) sin llamadas de red.
- [x] #7 `uv run pytest` pasa en la suite relevante; sin regresiones obvias en tests del agente.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Crear `src/api/tracing_langchain.py` con `aplicar_tracing_langchain_desde_config(cfg: Configuracion) -> None` y logging estructurado breve.
2. Anadir campos de tracing a `Configuracion` con `Field(validation_alias=...)` y descripciones que remitan al ADR decision-5.
3. Importar y llamar al helper al inicio de `lifespan` (tras `obtener_configuracion()`), antes de `construir_grafo_agente_produccion_o_none`.
4. Extender el `config` dict en `src/api/routers/agente.py` para `astream_events` con `metadata` segun criterios de privacidad.
5. Actualizar `.env.example` con bloque comentado LangSmith/LangChain tracing.
6. Anadir `tests/api/test_tracing_langchain.py` con `monkeypatch` / `obtener_configuracion.cache_clear()` segun patron del repo.
7. Ejecutar `uv run pytest tests/api/test_tracing_langchain.py` y suite acotada si hace falta; marcar AC y DoD al cerrar la tarea (`status: Done` sin archivar).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **DRY / SOLID**: un solo punto de aplicacion de variables (`aplicar_tracing_langchain_desde_config`); routers no duplican logica de entorno.
- **Por que escribir `os.environ`**: LangChain/LangSmith consultan variables de proceso; valores solo cargados en el modelo Pydantic no siempre se reexportan al entorno del proceso.
- **Dependencia `langsmith`**: puede seguir como transitiva de `langchain-core`; fijar version directa en `pyproject.toml` solo si el equipo necesita pin explicito (opcional, no bloqueante para esta tarea).
- Tras editar `.env`, recordatorio: `obtener_configuracion()` esta cacheada con `lru_cache`; reiniciar Uvicorn para releer valores.
- Correlacion futura con `request_id`: el middleware `middleware_request_id` existe; enlazar en una tarea posterior si se requiere el mismo id en LangSmith y en logs.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se implementó observabilidad LangSmith/LangChain de forma opcional: campos en `Configuracion` con alias `LANGCHAIN_*`, helper DRY `aplicar_tracing_langchain_desde_config` en `src/api/tracing_langchain.py` invocado al inicio del `lifespan` antes del grafo, bloque documentado en `.env.example`, `metadata` en `astream_events` con `usuario_id_interno` (UUID de aplicación, sin doc_id ni nombre), y tests `tests/api/test_tracing_langchain.py`. Suite `tests/api/`: 35 passed.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Criterios de aceptacion marcados segun estado real al cierre.
- [x] #2 Codigo alineado a convenciones del repo (identificadores Python en espanol ASCII; comentarios en español latinoamericano).
- [x] #3 Sin secretos en `backlog/tasks/` ni en comentarios de codigo; claves solo vía `.env`.
- [x] #4 `uv run pytest` verde para los tests nuevos y los existentes afectados.
- [x] #5 `status: Done` al finalizar (sin `task_complete` / sin mover a `completed/` salvo pedido explicito).
<!-- DOD:END -->
