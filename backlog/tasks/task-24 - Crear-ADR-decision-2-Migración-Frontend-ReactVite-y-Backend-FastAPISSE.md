---
id: TASK-24
title: 'Crear ADR decision-2: Migración Frontend React+Vite y Backend FastAPI+SSE'
status: Done
assignee: []
created_date: '2026-04-30 05:43'
updated_date: '2026-05-01 01:21'
labels:
  - adr
  - docs
  - frontend
  - api
dependencies:
  - TASK-21
priority: high
ordinal: 17
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El proyecto tiene un ADR (decision-1) que documenta el MVP BM25 a nivel archivo. La decisión de migrar de Gradio a React+Vite y añadir FastAPI+SSE es igualmente significativa y debe registrarse como ADR para mantener la trazabilidad de decisiones arquitectónicas.

## Objetivo

Crear `backlog/decisions/decision-2 - Migracion-Frontend-React-Vite-Backend-FastAPI-SSE.md` con:
- Contexto: limitaciones de Gradio para producción, demanda de UI de alto impacto visual
- Decisión: React 19 + Vite 7 + TypeScript + Tailwind v4 + shadcn/ui + FastAPI + SSE
- Consecuencias positivas y negativas
- Alternativas consideradas: Next.js (descartada por overhead SSR), Streamlit (descartada por similitud con Gradio), WebSockets (descartados en favor de SSE para streaming unidireccional)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Archivo decision-2 - Migracion-Frontend-React-Vite-Backend-FastAPI-SSE.md creado en backlog/decisions/
- [ ] #2 Front matter YAML con id: decision-2, title, date: '2026-04-30', status: accepted
- [ ] #3 Cuerpo con secciones Contexto, Decisión, Consecuencias (positivas y negativas), Alternativas consideradas
- [ ] #4 Nombra versiones exactas: React 19, Vite 7, TypeScript 5, Tailwind v4, FastAPI, sse-starlette
- [ ] #5 Referencia decision-1 como contexto previo
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
ADR decision-2 creado en backlog/decisions/ con front matter YAML completo (id, title, date: 2026-04-30, status: accepted). Cuerpo con secciones Contexto (limitaciones de Gradio), Decisión (FastAPI+SSE + React+Vite), Consecuencias (positivas y negativas), Alternativas consideradas (Next.js, Streamlit, WebSockets, Django, Litestar) y Referencias cruzadas a doc-001, doc-002 y decision-1.
<!-- SECTION:FINAL_SUMMARY:END -->
