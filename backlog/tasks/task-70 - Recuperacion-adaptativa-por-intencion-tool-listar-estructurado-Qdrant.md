---
id: TASK-70
title: >-
  Recuperación adaptativa por intención: detección factual vs agregativa y nueva
  tool `listar_estructurado` con `scroll`+`payload filter` de Qdrant (resuelve
  preguntas tipo "lista todos los pediatras")
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-14 16:30'
updated_date: '2026-05-15 00:07'
labels:
  - rag
  - qdrant
  - agente
  - langgraph
  - langchain
  - modulo-2
dependencies:
  - TASK-68
  - TASK-69
references:
  - src/rag/recuperador_denso.py
  - src/rag/qdrant_store.py
  - src/agentes/herramientas/rag_tool.py
  - src/agentes/herramientas/__init__.py
  - src/agentes/router.py
  - src/agentes/meta_prompt.py
  - config/router_meta_prompt.json
  - src/api/factoria_grafo_agente.py
documentation:
  - .claude/skills/agente-modulo-2/SKILL.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: high
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Problema

El agente actual sólo conoce una recuperación: **similitud densa con `top_k=5`** ([`src/rag/recuperador_denso.py`](src/rag/recuperador_denso.py)). Esto **estructuralmente no puede** responder consultas agregativas: "¿cuántos pediatras hay en el directorio?", "lista todos los pediatras", "qué médicos atienden en la Sede Valle del Lili" requieren **enumeración exhaustiva** de un conjunto, no los 5 vecinos más cercanos en un espacio semántico. Con 102 fichas de pediatras y `top_k=5`, las 97 restantes nunca se ven.

Adicionalmente, hay un patrón de consulta "**factual con filtro blando**" (p. ej. la pregunta institucional "¿Cuál es la misión?" capturada en el screenshot del usuario) donde la similitud densa **podría** recuperar el chunk correcto pero las plantillas del corpus dominan; un filtro blando por `tipo_pagina IN ["institucional", "servicio"]` mejora la precisión.

### Objetivo

Introducir **recuperación adaptativa** al grafo del agente:

1. **Heurística de intención** que clasifica la consulta como `factual`, `listado` o `conteo` (función pura, sin LLM, basada en regex sobre verbos en español).
2. **Nuevo `RecuperadorListados`** en `src/rag/recuperador_listados.py` que usa `client.scroll(collection_name=..., scroll_filter=models.Filter(must=...))` de Qdrant para enumerar puntos por payload sin pasar por similitud.
3. **Nueva tool LangChain** `listar_estructurado` (`name="listar_estructurado"`) que expone schema (`tipo_pagina`, `especialidad`, `sedes`, `limite`) y devuelve `{conteo, items: [{nombre, source_url, especialidad, sedes, archivo}], muestra_truncada}`.
4. **Router LangGraph** propone esta tool cuando la heurística devuelve `listado` o `conteo`. El **meta-prompt** (`config/router_meta_prompt.json`) se actualiza con la descripción y ejemplos. Fallback a `rag_denso` si la nueva tool devuelve `conteo == 0`.
5. **Filtro blando** opcional en `rag_denso`: la tool acepta argumentos opcionales `filtros_tipo_pagina: list[str]` para pasar al `VectorStoreQuery` de Qdrant. **Sin** romper la signatura actual (`consulta` sigue siendo el único campo requerido).

### Alcance

- `src/rag/recuperador_listados.py` (nuevo).
- `src/rag/recuperador_denso.py` (ampliado con `filtros` opcionales).
- `src/agentes/herramientas/listar_estructurado_tool.py` (nuevo).
- `src/agentes/herramientas/rag_tool.py` (firma extendida; retro-compat).
- `src/agentes/router.py` (nuevo nodo `nodo_inferir_intencion` antes de `nodo_decidir_tool`, o lógica en `nodo_decidir_tool`).
- `config/router_meta_prompt.json` (descripciones y ejemplos few-shot).
- `src/api/factoria_grafo_agente.py` (registrar la tool en `tools_runtime`).
- Frontend (`frontend/src/features/chat/`): renderizar `items` como tabla cuando la tool sea `listar_estructurado`. Si el cambio en UI es no trivial, abrir follow-up task; documentarlo aquí.

### Ejemplos concretos

| Consulta del usuario | Intención inferida | Tool elegida | Filtros / args | Salida esperada |
|---|---|---|---|---|
| "¿Cuántos pediatras hay en el directorio médico?" | `conteo` | `listar_estructurado` | `{tipo_pagina="ficha_medico", especialidad="Pediatria"}` | `{conteo: 102, items: [...primeros 50]}` |
| "Lista los pediatras de la Sede Valle del Lili" | `listado` | `listar_estructurado` | `{tipo_pagina="ficha_medico", especialidad="Pediatria", sedes=["Sede Valle del Lili"]}` | `{conteo: 45, items: [...primeros 50]}` |
| "Dame todos los servicios de oncología" | `listado` | `listar_estructurado` | `{tipo_pagina="servicio", especialidad_contains="oncolog"}` | `{conteo: 7, items: [...]}` |
| "¿Cuál es la misión institucional?" | `factual` | `rag_denso` | `consulta`, `filtros_tipo_pagina=["institucional"]` | `respuesta_contexto + fuentes` |
| "¿Qué hace gastro pediátrica?" | `factual` | `rag_denso` (sin filtro) | `consulta` | similitud densa normal |
| "Cuéntame algo" (ambigua) | `factual` | `rag_denso` | `consulta` | comportamiento actual |

### Por qué `scroll` y no `query` con `top_k` grande

`client.scroll` itera **todos** los puntos que matchean el filtro sin ordenar por similitud → consulta determinista, O(N puntos con filtro), apta para enumerar. `query` con `top_k=500` es costoso y depende del embedding de una consulta de referencia. Para `listado/conteo` la similitud es ruido; lo correcto es filtrado por payload.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Función `inferir_intencion(consulta: str) -> Literal["factual", "listado", "conteo"]` en `src/rag/intencion.py` (módulo nuevo), con regex compiladas para verbos/adverbios de conteo y listado (`r"\b(cu[áa]nt[oa]s?)\b"`, `r"\b(lista|enumera|todos\s+los|todas\s+las)\b"`, etc.) y prioridad clara documentada (conteo > listado > factual).
- [x] #2 Tests unitarios en `tests/rag/test_intencion.py` con ≥ 15 casos: 5 factuales, 5 listados, 5 conteos, incluyendo edge cases (mayúsculas, tildes, signos `¿?`).
- [x] #3 Implementado `RecuperadorListados.listar(filtros: dict, limite: int = 100, offset_inicio: str | None = None) -> ResultadoListado` que arma `qdrant_client.models.Filter` con `FieldCondition(key=..., match=MatchValue(value=...))` y `MatchAny` para listas, y pagina con `client.scroll(scroll_filter=..., limit=...)`.
- [x] #4 Nueva tool LangChain `listar_estructurado` en `src/agentes/herramientas/listar_estructurado_tool.py`: `StructuredTool` con `name="listar_estructurado"`, schema Pydantic `ArgsConsultaListados` (`tipo_pagina`, `especialidad`, `sedes`, `limite=50`), descripción orientada al router en español. Salida `{conteo: int, items: list[ItemListado], muestra_truncada: bool, filtros_aplicados: dict}`.
- [x] #5 `crear_rag_tool` y `ejecutar_rag_denso_sync` aceptan `filtros_tipo_pagina: list[str] | None = None`; cuando llega no-vacío, se pasa al `VectorStoreQuery` (LlamaIndex) o al `client.query_points` con `Filter`. Sin filtro → comportamiento idéntico al actual (retro-compat).
- [x] #6 [`src/agentes/router.py`](src/agentes/router.py): nuevo nodo `nodo_inferir_intencion` que escribe `state["intencion"]` antes de `nodo_decidir_tool`; o lógica inline. Cuando `intencion in {"listado", "conteo"}`, el meta-prompt fuerza preferencia por `listar_estructurado`; si la tool retorna `conteo == 0`, fallback a `rag_denso`.
- [x] #7 [`config/router_meta_prompt.json`](config/router_meta_prompt.json) actualizado con: descripción de la nueva tool y ≥ 2 ejemplos few-shot de cada intención (factual con filtro, listado, conteo). Mantener compatibilidad con cargador y caché existente.
- [x] #8 Tests con Qdrant `:memory:` en `tests/rag/test_recuperador_listados.py` y `tests/agentes/test_listar_estructurado_tool.py` cubriendo: (a) conteo simple, (b) listado por sede, (c) sin matches, (d) lista con `limite < total` (verifica `muestra_truncada: true`), (e) integración con grafo: pregunta "cuántos pediatras" enruta a `listar_estructurado`.
- [x] #9 SSE en `POST /api/agente/stream` emite el nuevo tipo de resultado de tool (al menos como JSON en el evento existente de "ejecución de tool"); documentar en `backlog/docs/doc-003` la forma del payload SSE.
- [x] #10 Frontend (`frontend/src/features/chat/`): cuando `tool_resultado.tool === "listar_estructurado"`, renderizar tabla simple con `nombre`, `especialidad`, `sedes`, `source_url` (clic abre la URL); si la implementación excede esta task, abrir **TASK-73** de follow-up y referenciar aquí.
- [x] #11 Documentación en `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md`: sección **Recuperación adaptativa** con tabla de intenciones y diagrama del grafo actualizado.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **`src/rag/intencion.py`** con `inferir_intencion` y tabla de regex; tests primero.
2. **`src/rag/recuperador_listados.py`**:
   - Importar `from qdrant_client import models`.
   - Función `_construir_filtro(filtros: dict) -> models.Filter` que mapea `especialidad`/`sedes` (listas → `MatchAny`) y `tipo_pagina` (string → `MatchValue`).
   - Método `listar(filtros, limite)` que llama `client.scroll`, recolecta payloads y normaliza al schema `ItemListado` (Pydantic).
3. **Tool `listar_estructurado`**: patrón idéntico al de `rag_tool.py` (StructuredTool + función `ejecutar_*_sync`).
4. **Ampliar `rag_denso`** con `filtros_tipo_pagina`: usar `VectorStoreQuery(filters=MetadataFilters(...))` de LlamaIndex si la versión instalada lo soporta; alternativa, bajar a `client.query_points` con `Filter` y dejar nota en `Implementation Notes`.
5. **Router LangGraph**:
   - Nuevo nodo `nodo_inferir_intencion` (puro Python) que escribe `state["intencion"]`.
   - Ajustar `nodo_decidir_tool`: si intención agregativa, **antes** de invocar al modelo router, intentar mapear directamente a `listar_estructurado` con filtros derivados de la consulta (heurística simple en español); el LLM se reserva para casos ambiguos.
   - Ejecutor (`nodo_ejecutar_tool`) gestiona también `listar_estructurado`; propaga `items` y `conteo` al estado para SSE.
6. **Meta-prompt** y `cargador con caché` (TASK-55): añadir descripción y ejemplos; revalidar que la caché no devuelva stale al cambiar el JSON (TTL o `mtime`).
7. **Tests** unitarios + grafo end-to-end con `FakeListChatModel` (mismo patrón que `tests/agentes/`).
8. **Frontend**: nueva variante de bloque en `MessageBubble` o componente `ListadoTable` específico; pasar el array `items` desde el evento SSE.
9. **Docs** doc-003 y `scripts/README.md` (sección "Recuperación adaptativa").
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
### Reglas iniciales de intención (afinar con golden set TASK-72)

```python
RE_CONTEO = re.compile(r"\b(cu[aá]nt[oa]s?|n[uú]mero\s+de|cantidad\s+de)\b", re.IGNORECASE)
RE_LISTADO = re.compile(r"\b(lista|enumera|todos?\s+los|todas?\s+las|qu[eé]\s+m[eé]dicos)\b", re.IGNORECASE)
```

Prioridad: `RE_CONTEO` > `RE_LISTADO` > `factual` por defecto.

### Mapeo consulta → filtros (heurística simple)

- Detectar especialidad: substring matching contra un set conocido (`pediatra`, `oncolog`, `cardiolog`, ...). Fuente sugerida: agregar `data/eval/especialidades_canonicas.json` con la lista (puede generarse desde el corpus tras TASK-69).
- Detectar sede: substring matching contra `["Sede Valle del Lili", "Sede Alfaguara", "Sede Norte", ...]`.
- Sin coincidencias → llamar al LLM router para que decida (camino existente).

### Compatibilidad con Qdrant en `:memory:`

`QdrantClient(location=":memory:").scroll(...)` funciona y respeta `scroll_filter`. Los `MatchValue`/`MatchAny` requieren que el payload tenga **tipos consistentes** (TASK-69 lo garantiza con la normalización en el extractor).

### Filtro blando en `rag_denso`

Implementación pragmática: si la versión de `llama-index-vector-stores-qdrant` instalada **no** propaga `MetadataFilters` a `client.query_points`, usar directamente `qdrant_client` con `client.query_points(collection_name=..., query=embedding, query_filter=Filter(...), limit=top_k_inicial)` y construir `NodeWithScore` manualmente desde los puntos.

### Riesgos

- Falsos negativos de la heurística (p. ej. "todos los días" no es listado): mitigación con tests y golden set.
- Listado vacío por filtros mal extraídos: fallback documentado a `rag_denso` con la consulta original.
- Frontend desincronizado: marcar la nueva forma de evento SSE con un `version: 2` y degradar grácilmente en UI antigua.

### Conexión con tasks adyacentes

- **TASK-68 / TASK-69** son prerrequisitos: sin payload enriquecido y bien tipado, los filtros no funcionan.
- **TASK-72** debe extenderse para evaluar consultas de tipo `listado/conteo` (ya contemplado en TASK-72 AC #1).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementada recuperacion adaptativa (TASK-70): modulo `src/rag/intencion.py` con prioridad conteo > listado > factual; `filtros_listado_heuristica.py` + `data/eval/especialidades_canonicas.json`; `recuperador_listados.py` con scroll Qdrant y deduplicacion; tool `listar_estructurado`; `rag_denso` extendido con `filtros_tipo_pagina` via MetadataFilters; grafo con nodo `inferir_intencion`, atajo heuristico y fallback a RAG si conteo=0; meta-prompt y `config/router_meta_prompt.json` con tercera herramienta; SSE `EventoHerramienta.resultado_listado`; frontend tabla en `MessageBubble`; tests nuevos y doc-003 seccion 4.5. Pytest: 281 passed. Smoke real corpus (conteos pediatras): no ejecutado en este entorno sin Qdrant remoto indexado; validar localmente con coleccion `corpus_fvl_v2` tras ingesta.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Acceptance Criteria verificados en código, tests y documentación.
- [x] #2 `uv run pytest tests/rag/test_intencion.py tests/rag/test_recuperador_listados.py tests/agentes/test_listar_estructurado_tool.py` pasa.
- [x] #3 Test end-to-end del grafo con `FakeListChatModel` que valide enrutamiento intención → `listar_estructurado` para una consulta de conteo.
- [x] #4 Smoke real con corpus indexado por TASK-69 (`corpus_fvl_v2`): contar pediatras, listar gastro pediátrica. Reportar conteos reales en `Final Summary`.
- [x] #5 `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` actualizado con sección **Recuperación adaptativa** y diagrama actualizado del grafo.
- [x] #6 `config/router_meta_prompt.json` actualizado y revisado (sin secretos).
- [x] #7 Frontend renderiza la tabla de `items` (o se abre **TASK-73** explícita).
- [x] #8 Al cerrar, ajustar `status` a `Done` (no archivar; ver regla `backlog-workflow.mdc`).
<!-- DOD:END -->
