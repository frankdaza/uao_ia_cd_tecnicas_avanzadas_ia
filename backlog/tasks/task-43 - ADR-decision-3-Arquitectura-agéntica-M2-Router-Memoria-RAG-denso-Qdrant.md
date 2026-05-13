---
id: TASK-43
title: 'ADR decision-3: Arquitectura agéntica M2 (Router + Memoria + RAG denso Qdrant)'
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-13 00:58'
labels:
  - adr
  - docs
  - modulo-2
  - agente
dependencies: []
references:
  - backlog/decisions/decision-1 - MVP-BM25-Archivo-Completo.md
  - >-
    backlog/decisions/decision-2 -
    Migracion-Frontend-React-Vite-Backend-FastAPI-SSE.md
  - >-
    backlog/docs/actividades/Técnicas Avanzadas de IA en Modelos de Lenguaje -
    Actividad del Módulo 2.pdf
  - .claude/skills/backlog-decisions/SKILL.md
documentation:
  - >-
    backlog/docs/actividades/Técnicas Avanzadas de IA en Modelos de Lenguaje -
    Actividad del Módulo 2.pdf
  - .claude/skills/backlog-decisions/SKILL.md
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
modified_files:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
  - backlog/decisions/decision-1 - MVP-BM25-Archivo-Completo.md
  - >-
    backlog/tasks/task-43 -
    ADR-decision-3-Arquitectura-agentica-M2-Router-Memoria-RAG-Qdrant.md
priority: high
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El Módulo 2 exige evolucionar el agente Lili hacia un sistema multi-capacidad: memoria persistente multiusuario, herramienta estructurada de FAQs, router agéntico y RAG semántico. El MVP del Módulo 1 (decision-1) documentó BM25 a nivel archivo completo; el equipo decidió **retirar BM25 del runtime productivo** y usar **solo recuperación densa en Qdrant** (sin fusión híbrida ni RRF), con embeddings parametrizables por `.env` (default OpenAI `text-embedding-3-small`, opción local HuggingFace). La sesión es **una conversación continua por usuario** identificado por documento de identidad y nombre, con ventana temporal configurable (`HISTORIAL_DIAS_MAX`, default 7 días).

## Objetivo

Crear el archivo `backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md` siguiendo la skill `backlog-decisions` (front matter YAML: `id`, `title`, `date`, `status: accepted` al aprobar el borrador).

El ADR debe justificar de forma explícita:

- **PostgreSQL** frente a SQLite para memoria y usuarios (durabilidad, concurrencia, integración con `langchain-postgres`).
- **Qdrant** frente a Chroma, PGVector o FAISS embebido (operación en Docker, rendimiento, cliente maduro, separación de concerns respecto a OLTP).
- **Combinación de frameworks**: LlamaIndex para RAG denso sobre Qdrant; **LangGraph** (`StateGraph`) para el router; **LangChain** para memoria (`PostgresChatMessageHistory`) y `StructuredTool`.
- **Eliminación de BM25 y ausencia de RAG híbrido**: simplicidad operativa, una sola fuente de verdad en recuperación, sin ajustar pesos/RRF, sin dependencias `rank-bm25` / `nltk` en producción; marcar **decision-1 como superseded** por esta decisión en lo que respecta al camino de recuperación en runtime.
- **Sesión continua** y parámetro `HISTORIAL_DIAS_MAX` para limitar mensajes inyectados al contexto del agente.

Incluir un diagrama **Mermaid** del flujo: Usuario → Router → Herramienta (FAQ o RAG) → LLM → Respuesta, con anotación de persistencia en PostgreSQL y vectores en Qdrant.

No incluir secretos ni API keys en el ADR.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [x] #1 Archivo `backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md` existe y cumple naming ASCII del skill backlog-decisions
- [x] #2 Front matter con `id: decision-3`, `title`, `date` ISO, `status` coherente (`accepted` cuando se apruebe el contenido)
- [x] #3 Secciones Contexto, Decisión, Consecuencias (positivas, negativas/riesgos, mitigación si aplica), Alternativas consideradas, Referencias
- [x] #4 Justifica PostgreSQL, Qdrant, stack LangGraph + LlamaIndex + LangChain-postgres y embeddings parametrizables (.env)
- [x] #5 Declara explícitamente retiro de BM25/híbrido y estado **superseded** de decision-1 respecto al runtime de recuperación; enlaza decision-2 como contexto de UI/API
- [x] #6 Diagrama Mermaid del flujo end-to-end solicitado
- [x] #7 Menciona `HISTORIAL_DIAS_MAX` y modelo de sesión continua por usuario
- [x] #8 Prosa en español latinoamericano; identificadores en ejemplos de código alineados a convenciones del repo
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Releer decision-1 y decision-2 para alinear numeración y referencias cruzadas.
2. Redactar borrador del ADR con todas las secciones obligatorias del skill.
3. Insertar diagrama Mermaid (flowchart o secuencia) Usuario → Login → API → Router → Tools → LLM → respuesta.
4. Revisión interna: coherencia con plan M2 (sin BM25 en runtime, Qdrant denso).
5. Fijar `status: accepted` y fechas finales en front matter.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- El ADR **no** sustituye la guía operativa larga: la task-62 (`doc-003`) amplía troubleshooting y comandos.
- Si el nombre del PDF en `backlog/docs/actividades/` difiere por encoding, referenciar la ruta real del repo sin pegar contenido privativo.
- No editar el archivo de plan `.cursor/plans/` al documentar; solo `backlog/decisions/`.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
ADR decision-3 creado (LangGraph + LangChain Postgres + LlamaIndex/Qdrant, sin BM25 en runtime M2, diagrama Mermaid, HISTORIAL_DIAS_MAX). decision-1 marcada superseded con nota de alcance. pytest: 125 passed, 1 skipped.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [x] #1 ADR mergeable en `backlog/decisions/` con skill backlog-decisions satisfecha
- [x] #2 `uv run pytest` y frontend tests no requieren cambio por solo-docs; si el CI valida markdown/lint, pasar sin errores nuevos
- [x] #3 Referencias cruzadas a decision-1 (superseded) y decision-2 verificables desde el markdown
<!-- DOD:END -->
