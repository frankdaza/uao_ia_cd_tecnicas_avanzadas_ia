---
id: TASK-94
title: >-
  Historial M2: metadatos del agente alineados con SSE (tool, razonamiento,
  fuentes Qdrant)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-16 18:31'
updated_date: '2026-05-16 18:38'
labels:
  - modulo-2
  - backend
  - frontend
  - postgres
  - historial
  - api-contract
dependencies: []
references:
  - src/agentes/router.py
  - src/agentes/estado.py
  - src/agentes/memoria/historial.py
  - src/api/routers/sesiones.py
  - src/api/esquemas.py
  - frontend/src/lib/schemas.ts
  - frontend/src/lib/api.ts
  - frontend/src/features/chat/Chat.tsx
  - frontend/src/features/chat/MessageBubble.tsx
  - frontend/src/features/chat/SourcesPanel.tsx
  - tests/agentes/test_router_grafo.py
  - >-
    backlog/tasks/task-59 -
    Refactor-del-Chat-al-endpoint-del-agente-historial-y-UI-de-herramientas-razonamiento.md
  - src/agentes/metadata_turno_historial.py
  - tests/agentes/test_metadata_turno_historial.py
  - tests/api/test_historial_metadata_turno.py
documentation:
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
  - .claude/skills/agente-modulo-2/SKILL.md
  - .claude/skills/fastapi-sse-api/SKILL.md
priority: medium
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
### Contexto

En la sesion actual, el chat muestra badges (Agente, Tool FAQ / RAG), duracion, panel Razonamiento del router (p. ej. faq_estructurada y justificacion corta) y fuentes vectoriales con enlaces y scores. Tras recargar o reabrir la sesion, GET /api/sesiones/actual/historial solo devuelve rol y texto: el historial pierde trazabilidad (soporte, auditoria, confianza).

Evidencia: captura de conversacion compartida por el equipo; si no esta en Git, enlazar en wiki o PR.

### Problema tecnico

- El grafo no serializa pensamientos en additional_kwargs del AIMessage al persistir (solo tool y fuentes en nodo_persistir_turno).
- _serializar_mensaje_lc en sesiones.py ignora additional_kwargs: el cliente no recibe tool ni fuentes.
- MensajeHistorialItem y HistorialMensajeSchema solo exponen rol, contenido, creado_en.

TASK-59 cubrio transparencia en vivo (SSE); esta tarea alinea historial persistido con la misma UX de datos.

### Objetivo

1. Persistir metadata estable y JSON-serializable (tool efectiva, pensamientos resumidos, fuentes RAG con score/source_url segun contrato RAG vigente).
2. Extender API de historial de forma retrocompatible (campos opcionales).
3. Frontend: hidratar historial al mismo modelo de UI que SSE (badges, panel colapsable, SourcesPanel).
4. Tests backend y frontend; documentar contrato breve (esquema o doc-003).

### Ejemplos de contrato (orientativos; nombres finales en PR)

Mensaje AI con FAQ: metadata_turno con motor agente, herramienta_efectiva faq_estructurada, pensamientos (tipo decision_router y ejecucion_tool con razon_breve), fuentes [].

Mensaje AI con RAG: fuentes como lista de dicts con archivo, titulo, source_url, score.

Mensaje humano: metadata_turno omitida o null.

**Ejemplo JSON (FAQ):**

```json
{
  "rol": "ai",
  "contenido": "Texto de la respuesta al usuario…",
  "creado_en": null,
  "metadata_turno": {
    "motor": "agente",
    "herramienta_efectiva": "faq_estructurada",
    "pensamientos": [
      {
        "tipo": "decision_router",
        "herramienta": "faq_estructurada",
        "razon_breve": "Selección vía tool binding del LLM del router según meta-prompt.",
        "argumentos_resumidos": { "consulta": "…" }
      },
      {
        "tipo": "ejecucion_tool",
        "herramienta": "faq_estructurada",
        "razon_breve": "Tool ejecutada; resultado disponible para el compositor."
      }
    ],
    "fuentes": []
  }
}
```

**Ejemplo JSON (RAG):**

```json
{
  "rol": "ai",
  "contenido": "…",
  "metadata_turno": {
    "motor": "agente",
    "herramienta_efectiva": "rag_denso",
    "pensamientos": [],
    "fuentes": [
      {
        "archivo": "fundacion/ejemplo.md",
        "titulo": "Título legible",
        "source_url": "https://ejemplo.org/doc",
        "score": 0.82
      }
    ]
  }
}
```

### No objetivos

- No reescribir LangGraph salvo lo minimo.
- No exponer prompts completos ni PII sin truncado; alinear con TASK-59.
- No migracion destructiva de chat_history; mensajes viejos sin metadata siguen mostrandose solo como texto.

### Riesgos y mitigaciones

| Riesgo | Mitigacion |
|--------|------------|
| JSON muy grande en Postgres | Tope y truncado documentado |
| Divergencia SSE vs historial | DTO o funcion pura de mapeo compartida |
| Clientes terceros | Campos opcionales |
<!-- SECTION:DESCRIPTION:END -->

## Buenas practicas TECH

Contrato API retrocompatible; validacion al leer desde DB; logs solo ante errores de serializacion; piramide de tests; limites de payload; aria-expanded en paneles; minimizar PII en metadata.

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tras un turno con FAQ (faq_estructurada), al recargar la app el mensaje del asistente muestra la misma categoria de tool que en streaming (badge o equivalente) y el panel de razonamiento contiene al menos la justificacion corta alineada con decision_router / ejecucion_tool.
- [x] #2 Tras un turno con RAG denso, al recargar se listan fuentes con enlace clicable cuando exista source_url y se muestra score o metrica de relevancia del contrato RAG vigente.
- [x] #3 GET /api/sesiones/actual/historial incluye en mensajes ai campos opcionales documentados para metadata del turno; mensajes antiguos sin metadata siguen validos y el frontend no falla.
- [x] #4 Retrocompatibilidad: respuesta JSON aceptada por esquema Pydantic v2 extendido sin romper clientes que solo lean rol y contenido.
- [x] #5 Paridad de datos: la metadata servida no contradice lo que el grafo habria emitido en SSE para el mismo turno (misma herramienta efectiva y mismas fuentes post-tool, salvo truncado documentado).
- [x] #6 Limites: si el contenido serializado excede umbral configurable o seguro por defecto, truncado explicito y señal en metadata sin silenciar errores de serializacion.
- [x] #7 Tests backend cubren serializacion de AIMessage con additional_kwargs hacia el DTO de historial (con metadata, sin metadata, fuentes multiples).
- [x] #8 Tests frontend (Vitest) validan parseo Zod del historial extendido y que el estado inicial del chat reconstruye tool, fuentes y pensamientos cuando vienen del API.
- [x] #9 uv run pytest pasa en los modulos tocados segun CI del repo.
- [x] #10 pnpm --dir frontend test pasa.
- [x] #11 Sin regresion en borrar ultimo turno ni en ventana temporal de MemoriaUsuario / chat_history.
- [x] #12 Documentacion: al menos una frase en doc de API o doc-003 enlazando el contrato del bloque de metadata del turno (nombre final del PR).
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Inventario: forma de fuentes y pensamientos en estado y SSE (agente.py, router.py).
2. Persistencia: extender nodo_persistir_turno con pensamientos en additional_kwargs; normalizacion serializable y truncado.
3. DTO FastAPI: extender MensajeHistorialItem y _serializar_mensaje_lc; tests api o agentes.
4. Frontend: HistorialMensajeSchema y mapeo en Chat / MessageBubble o hook; reutilizar UI SSE.
5. Hardening: Pydantic en subestructuras; filas legacy sin metadata.
6. E2E opcional Playwright si el pipeline lo tolera.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- DRY: metadata_turno_desde_estado(state) o equivalente solo en persistencia.
- Seguridad: no volcar prompts ni datos clinicos no aprobados en pensamientos.
- UI en espanol latinoamericano; identificadores TS en ingles; Python identificadores ASCII sin ene ni tildes.
- Documentar nombre final del bloque metadata (evitar ambiguedad tool vs herramienta_efectiva).
- Sin backfill obligatorio de filas antiguas.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementacion TASK-94: modulo src/agentes/metadata_turno_historial.py (construir + normalizar con saneo y limites de tamano); nodo_persistir_turno persiste metadata_turno junto a tool/fuentes legacy; GET historial expone MetadataTurnoHistorial en MensajeHistorialItem; frontend hidrata toolUsed, routerThoughts y ragSources desde metadata_turno; pruebas pytest (serializacion, grafo FAQ/RAG) y Vitest (schemas + Chat). Documentacion en doc-003 seccion memoria (historial HTTP). Smoke manual F5 y DoD item 3 quedan para verificacion humana en entorno integrado.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 PR revisado; sin secretos ni datos personales nuevos en logs o payloads de ejemplo.
- [x] #2 OpenAPI o esquema FastAPI actualizado si el repo exporta schema y es parte del CI.
- [ ] #3 Smoke manual: login, pregunta FAQ, F5, verificar UI; pregunta RAG, F5, verificar fuentes y scores.
- [x] #4 Changelog o nota en PR para consumidores que solo usen rol/contenido (campos nuevos opcionales).
<!-- DOD:END -->
