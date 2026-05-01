---
id: TASK-21
title: >-
  Actualizar reglas Cursor para stack React+Vite/FastAPI+SSE y excepción TS en
  language-conventions
status: Done
assignee: []
created_date: '2026-04-30 05:42'
updated_date: '2026-05-01 01:20'
labels:
  - rules
  - frontend
  - api
  - docs
dependencies: []
priority: high
ordinal: 20
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El proyecto migra su interfaz de Gradio a React 19 + Vite 7 + TypeScript + Tailwind v4 + shadcn/ui, con un backend FastAPI + SSE en `src/api/`. Las reglas Cursor actuales en `.cursor/rules/` solo cubren el stack Python (Gradio, Ollama). Hay que actualizar las reglas existentes y crear dos nuevas para guiar a los agentes en el nuevo stack.

## Objetivo

1. Actualizar `project-stack.mdc`: reemplazar la sección «Interfaz de prueba: Gradio» por React+Vite+shadcn+Vercel AI SDK y añadir sección «Backend HTTP: FastAPI + SSE».
2. Actualizar `project-structure.mdc`: añadir `frontend/` y `src/api/`; documentar build estático servido por FastAPI.
3. Actualizar `language-conventions.mdc`: añadir excepción explícita para `frontend/**/*.{ts,tsx,js,jsx}` donde los identificadores se mantienen en inglés (convención del ecosistema React/TS).
4. Crear `.cursor/rules/frontend-style.mdc` (glob `frontend/**/*.{ts,tsx,js,jsx,css}`): Tailwind v4, shadcn/ui, ESLint v9 flat config, Prettier, convenciones de carpetas, naming, React Query.
5. Crear `.cursor/rules/api-fastapi.mdc` (glob `src/api/**/*.py`): patrones SSE con `sse-starlette`, errores normalizados RFC 7807, dependencias inyectables, Pydantic v2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 project-stack.mdc actualizado: Gradio → React 19 + Vite 7 + shadcn/ui + Vercel AI SDK; nueva sección FastAPI + SSE con uvicorn y sse-starlette
- [ ] #2 project-structure.mdc incluye frontend/ y src/api/ con descripción de cada subcarpeta; documenta build estático servido por FastAPI en producción
- [ ] #3 language-conventions.mdc contiene excepción explícita: en frontend/**/*.{ts,tsx,js,jsx} los identificadores usan inglés; UI visible y comentarios en español-LATAM
- [ ] #4 frontend-style.mdc creado con glob frontend/**/*.{ts,tsx,js,jsx,css}: Tailwind v4, shadcn CLI, ESLint v9 flat, Prettier, estructura de carpetas features/components/hooks/lib
- [ ] #5 api-fastapi.mdc creado con glob src/api/**/*.py: patrones SSE, Pydantic v2, errores RFC 7807, inyección de dependencias con Depends
- [ ] #6 Todos los archivos .mdc en UTF-8 y sin errores de parseo YAML
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Actualizado project-stack.mdc (Gradio → React 19+Vite 7+shadcn/ui+FastAPI+SSE), project-structure.mdc (frontend/ y src/api/ con subcarpetas detalladas), language-conventions.mdc (excepción TS/JS: identificadores en inglés en frontend/**). Creados frontend-style.mdc (glob frontend/**) y api-fastapi.mdc (glob src/api/**) con convenciones completas de cada capa.
<!-- SECTION:FINAL_SUMMARY:END -->
