---
id: TASK-96
title: 'ADR decision-4: arquitectura M3 TAAM en proyecto-2 (Ruta A, Telegram vía 2)'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:15'
labels:
  - modulo-3
  - taam
  - adr
  - telegram
  - proyecto-2
milestone: m-0
dependencies: []
references:
  - >-
    backlog/docs/actividades/Actividad del Módulo 3_ Productización, Despliegue
    Avanzado y Sistemas Agénticos.md
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - proyecto-1/
documentation:
  - .claude/skills/backlog-decisions/SKILL.md
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El MVP **Bot posoperatorio TAAM** (Fundación Valle del Lili) se entrega en **Módulo 3** con **Ruta A** (LangChain function calling estricto, FastAPI, **Telegram**) y **vía 2** (servidor de integración propio, sin N8N). El código M2 productivo permanece en `proyecto-1/`; TAAM debe vivir en **`proyecto-2/`** para no mezclar runtime LangGraph M2 con el stack obligatorio del curso (`create_agent`, `PostgresSaver`, `HumanInTheLoopMiddleware`).

## Objetivo

Registrar la decisión arquitectónica **decision-4** y un diagrama end-to-end que fije límites del MVP antes de codificar.

## Contenido obligatorio del ADR

1. **Problema:** seguimiento postoperatorio vía Bot Lili; canal demo = Telegram.
2. **Decisión:** carpeta `proyecto-2/`; API `POST /chat`; webhook Telegram en el mismo FastAPI; Postgres + Qdrant (colección dedicada TAAM); frontend React **nuevo** con branding M2.
3. **Relación con M2:** qué se reutiliza (patrones RAG, `UAO_WORKSPACE_ROOT`, `data/`) y qué **no** se porta (grafo LangGraph de `proyecto-1/src/agentes/router.py`).
4. **Stack LangChain exigido en rúbrica:** lista verificable (`init_chat_model`, `create_agent`, `HumanInTheLoopMiddleware`, `RecursiveCharacterTextSplitter`, vector stores LangChain, `dynamic_prompt`, `PostgresSaver`).
5. **Sesiones:** `session_id` canónico `telegram:{chat_id}`; vínculo paciente↔chat en tabla aparte.
6. **Fuera de MVP:** RBAC completo, email de citas, evidencias multimedia, intervención en vivo en Telegram.
7. **Riesgos aceptados:** PDF no garantiza extracción perfecta de horarios; recordatorios por plantilla + fecha cirugía.

## Diagramas

Incluir al menos: contexto (actores), secuencia Telegram→webhook→`/chat`→agente→Postgres/Qdrant, despliegue docker.

## Entregables

- `backlog/decisions/decision-4 - Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md` con front matter estilo Backlog.
- Enlace desde `backlog/milestones/m-0 - agentic-final-project.md` y nota en plan de casos de uso.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Existe decision-4 con front matter YAML válido (id, title, type, created_date)
- [ ] #2 El ADR documenta explícitamente Ruta A + Telegram vía 2 y separación proyecto-1 vs proyecto-2
- [ ] #3 Incluye diagrama mermaid end-to-end y tabla de componentes con rutas de código previstas
- [ ] #4 Lista herramientas LangChain MVP y criterio de verificación en repo (grep/CI)
- [ ] #5 Milestone m-0 referencia decision-4 o el doc de casos de uso TAAM
<!-- AC:END -->
