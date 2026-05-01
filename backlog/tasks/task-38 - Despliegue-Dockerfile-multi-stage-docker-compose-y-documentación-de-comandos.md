---
id: TASK-38
title: 'Despliegue: Dockerfile multi-stage, docker-compose y documentación de comandos'
status: Done
assignee: []
created_date: '2026-04-30 05:46'
updated_date: '2026-05-01 01:18'
labels:
  - devops
  - docker
  - deployment
dependencies:
  - TASK-37
priority: medium
ordinal: 3
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Preparar el proyecto para despliegue reproducible:

- `Dockerfile` multi-stage: Stage 1 (node:22-alpine) build de frontend/; Stage 2 (python:3.12-slim) instala uv, copia src/ y dist/, sirve estáticos con FastAPI StaticFiles
- `docker-compose.yml`: servicios api (FastAPI), ollama (ollama/ollama), volumes para data/markdown y modelos Ollama
- `.env.example` actualizado: añadir ALLOWED_ORIGINS, API_PORT (defecto 8000), VITE_API_BASE (defecto /api)
- `Makefile` o scripts README: targets dev, build, docker-build, docker-up
- Documentar en README.md: modo dev (2 terminales) y modo producción (Docker)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 docker build -t qa-valledellili . sin errores
- [ ] #2 docker-compose up arranca api + ollama juntos
- [ ] #3 FastAPI sirve index.html del frontend en GET /
- [ ] #4 FastAPI sirve assets de frontend en /assets/*
- [ ] #5 Variable ALLOWED_ORIGINS en .env controla CORS
- [ ] #6 .env.example actualizado con las nuevas variables
- [ ] #7 README.md sección Despliegue documenta ambos modos (dev y Docker)
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Dockerfile multi-stage: Stage 1 node:22-alpine (pnpm build frontend/dist/), Stage 2 python:3.12-slim (uv sync + src/ + frontend/dist/ + StaticFiles). docker-compose.yml: servicios api (FastAPI port 8000) + ollama (ollama/ollama, healthcheck, volume ollama-models). .env.example actualizado: ALLOWED_ORIGINS, API_PORT. Notas en README.md con comandos docker-compose up.
<!-- SECTION:FINAL_SUMMARY:END -->
