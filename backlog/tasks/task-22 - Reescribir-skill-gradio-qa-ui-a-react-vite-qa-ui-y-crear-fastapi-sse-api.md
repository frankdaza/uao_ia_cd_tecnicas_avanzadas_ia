---
id: TASK-22
title: Reescribir skill gradio-qa-ui a react-vite-qa-ui y crear fastapi-sse-api
status: Done
assignee: []
created_date: '2026-04-30 05:42'
updated_date: '2026-04-30 05:52'
labels:
  - skills
  - frontend
  - api
dependencies:
  - TASK-21
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Las skills actuales en `.cursor/skills/` y `.claude/skills/` todavía documentan el patrón Gradio. Hay que reescribir la skill `gradio-qa-ui` y crear dos nuevas para el stack React+Vite y FastAPI+SSE.

## Objetivo

1. Reescribir `gradio-qa-ui/SKILL.md` → `react-vite-qa-ui/SKILL.md` en ambas carpetas: estructura de carpetas, patrón `useChat` con transport SSE, render Markdown, modo dual, comandos de desarrollo.
2. Crear skill `fastapi-sse-api/SKILL.md` en ambas carpetas: bootstrap FastAPI con uv, patrones SSE con sse-starlette, CORS, esquemas Pydantic, tests con httpx + ASGI transport.
3. Actualizar `llm-backend/SKILL.md` en ambas carpetas: añadir nota sobre exposición vía SSE y reutilización de métodos stream del PipelineQa.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 react-vite-qa-ui/SKILL.md existe en .cursor/skills/ Y .claude/skills/ con contenido idéntico
- [ ] #2 fastapi-sse-api/SKILL.md existe en .cursor/skills/ Y .claude/skills/ con contenido idéntico
- [ ] #3 llm-backend/SKILL.md actualizado en ambas carpetas con sección SSE
- [ ] #4 Skill gradio-qa-ui NO se elimina físicamente (se mantiene como legacy hasta task-39) pero el SKILL.md se marca como deprecado con nota
- [ ] #5 Todos los SKILL.md tienen front matter YAML con name y description
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Creadas skills react-vite-qa-ui y fastapi-sse-api en .cursor/skills/ y .claude/skills/ con contenido idéntico. Skill gradio-qa-ui marcada como deprecada en ambas carpetas. llm-backend actualizado con sección de exposición vía SSE y métodos del PipelineQa relevantes.
<!-- SECTION:FINAL_SUMMARY:END -->
