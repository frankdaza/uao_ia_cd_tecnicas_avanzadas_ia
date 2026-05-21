---
id: TASK-116
title: doc-004 Arquitectura M3 TAAM y evolución M2→proyecto-2 (informe + diagramas)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
labels:
  - modulo-3
  - taam
  - documentacion
  - informe
milestone: m-0
dependencies:
  - TASK-114
  - TASK-96
documentation:
  - .claude/skills/backlog-docs/SKILL.md
priority: medium
ordinal: 2200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Entregable 10% documentación técnica final del taller M3: comparar M2 vs M3, justificar Telegram vía 2 y stack LangChain.

## Objetivo

Crear `backlog/docs/doc-004 - Arquitectura-M3-Bot-Posoperatorio-TAAM.md` (siguiente N libre en docs).

## Contenido

1. Problema y solución TAAM (resumen).
2. Tabla comparativa: proyecto-1 (LangGraph SSE) vs proyecto-2 (create_agent, /chat, Telegram).
3. Diagrama end-to-end final (refleja código real post TASK-114).
4. Matriz cumplimiento rúbrica M3 (checkbox por requisito LangChain).
5. Limitaciones MVP y trabajo futuro (Fase 2 del doc UC).
6. Enlaces a decision-4, casos de uso, GUION demo.
7. Nota t-SNE opcional (solo si se implementa bonus).

## Informe LaTeX

Si el curso exige PDF unificado: sección M3 en `proyecto-2/informe/` o ampliar informe existente — al menos outline en esta tarea.

## Fallas a evitar

- Diagrama que no coincide con puertos/servicios reales del compose.
- Afirmar uso de N8N o WhatsApp si el proyecto es Telegram vía 2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 doc-004 existe con front matter id/title/type/created_date válido
- [ ] #2 Incluye diagrama mermaid y tabla M2 vs M3
- [ ] #3 Referencia decision-4 y los 5 UC-MVP
- [ ] #4 Lista verificable de componentes LangChain exigidos por el curso
- [ ] #5 Milestone m-0 o README enlaza doc-004
<!-- AC:END -->
