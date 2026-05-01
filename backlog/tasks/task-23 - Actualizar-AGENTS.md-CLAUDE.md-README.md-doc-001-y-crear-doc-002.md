---
id: TASK-23
title: 'Actualizar AGENTS.md, CLAUDE.md, README.md, doc-001 y crear doc-002'
status: Done
assignee: []
created_date: '2026-04-30 05:43'
updated_date: '2026-05-01 01:20'
labels:
  - docs
  - frontend
  - api
dependencies:
  - TASK-21
  - TASK-22
priority: high
ordinal: 18
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La documentación principal del repositorio (AGENTS.md, CLAUDE.md, README.md) y el doc-001 todavía referencian Gradio como única interfaz. Hay que actualizarlos para reflejar el nuevo stack React+Vite + FastAPI.

## Objetivo

1. `AGENTS.md`: actualizar tablas Stack y Skills; reemplazar gradio-qa-ui por react-vite-qa-ui; añadir fastapi-sse-api, frontend-style.mdc y api-fastapi.mdc.
2. `CLAUDE.md`: espejar los cambios de stack y skills.
3. `README.md`: sustituir sección «Cómo correr la app» por instrucciones duales (pnpm dev + uvicorn); actualizar Experiencia en la UI y Guía de demo.
4. `backlog/docs/doc-001`: añadir nota al final indicando que el frontend evoluciona a React+Vite en doc-002.
5. Crear `backlog/docs/doc-002 - Migracion-Frontend-React-Vite-Backend-FastAPI.md`: guía arquitectónica con diagramas mermaid, contratos de API, estructura de frontend/.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 AGENTS.md actualizado: tabla Stack sin Gradio, con React+Vite+shadcn y FastAPI+SSE; tabla Skills con react-vite-qa-ui y fastapi-sse-api
- [ ] #2 CLAUDE.md espeja exactamente los mismos cambios de Stack y Skills
- [ ] #3 README.md sección Cómo correr la app contiene comandos duales: uv run uvicorn src.api.main:app --reload y pnpm --dir frontend dev
- [ ] #4 doc-001 tiene nota al final de sección 2 o al pie referenciando doc-002
- [ ] #5 doc-002 existe con front matter id/title/type/created_date correcto y cuerpo con diagrama mermaid de la arquitectura objetivo y contratos de los 6 endpoints
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
AGENTS.md actualizado (Stack + Skills con React+Vite, FastAPI+SSE, rutas nuevas), CLAUDE.md espejado, README.md con instrucciones duales (uvicorn + pnpm dev), guía de demo actualizada para React. doc-001 tiene nota de evolución en sección 11 referenciando doc-002 y ADR-002. doc-002 creado con arquitectura completa, contratos de 7 endpoints, estructura de frontend/, paleta de colores institucional y comandos canónicos.
<!-- SECTION:FINAL_SUMMARY:END -->
