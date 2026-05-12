---
id: TASK-45
title: docker-compose.yml con PostgreSQL 16, Qdrant, healthchecks y volúmenes nombrados
status: To Do
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-11 00:00'
labels:
  - docker
  - infra
  - modulo-2
dependencies:
  - TASK-44
references:
  - docker-compose.yml
  - Dockerfile
  - src/api/main.py
documentation:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
  - README.md
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El Módulo 2 requiere **PostgreSQL 16** para usuarios y `chat_history`, y **Qdrant 1.x** para vectores del corpus. El servicio `api` debe esperar a que las dependencias estén saludables antes de exponer tráfico.

## Objetivo

Actualizar `docker-compose.yml` para incluir:

- **`postgres`**: imagen `postgres:16-alpine`, variables de entorno estándar, volumen nombrado `postgres-data`, healthcheck `pg_isready`.
- **`qdrant`**: imagen `qdrant/qdrant:v1.12.x` (o pin explícito acorde a compatibilidad con `qdrant-client`), puertos **6333/6334**, volumen `qdrant-storage`, healthcheck HTTP o comando recomendado por la imagen.
- **`db-init`**: servicio tipo job que ejecuta `alembic upgrade head` cuando `postgres` está saludable (patrón `depends_on` + `condition: service_healthy` o entrypoint que reintente).
- **`qdrant-init`** (opcional): job que crea la colección si no existe (puede delegarse al código Python en lifespan; documentar la opción elegida).
- **`api`**: `depends_on` postgres saludable, qdrant saludable y `db-init` completado; montajes de solo lectura: `./config:/app/config:ro`, `./data/structured:/app/data/structured:ro` (y corpus markdown solo si el contenedor indexa; por defecto no es necesario en runtime API).

Actualizar **`Dockerfile`** si hace falta para copiar `config/`, `data/structured/`, `alembic/` al contexto de la imagen.

## Verificación manual

`docker compose down -v && docker compose up --build` → servicios en verde; `curl` a `GET /api/salud` responde OK cuando la API esté lista.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 Servicios `postgres` y `qdrant` con healthchecks y volúmenes persistentes nombrados
- [ ] #2 Job `db-init` (o equivalente) ejecuta migraciones Alembic contra Postgres sano
- [ ] #3 Servicio `api` no arranca antes de dependencias salvo documentación explícita de desarrollo
- [ ] #4 Volúmenes `./config` y `./data/structured` montados ro en `api` según plan
- [ ] #5 `Dockerfile` incluye artefactos necesarios (`alembic/`, `config/`, `data/structured/`) si la imagen los requiere
- [ ] #6 Documentación breve en README o comentarios YAML sobre puertos y variables requeridas
- [ ] #7 `docker compose up` + smoke `curl` salud documentado en Implementation Notes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Diseñar grafo de dependencias entre servicios y nombres de red interna.
2. Añadir servicios postgres y qdrant con versiones pinneadas.
3. Implementar `db-init` con imagen que tenga `uv`/`alembic` o reutilizar stage builder del Dockerfile.
4. Ajustar `api` service: env vars desde `.env`, `depends_on` con condiciones.
5. Probar ciclo completo local; ajustar Dockerfile multi-stage si el stage final no tenía alembic.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- En desarrollo local sin Docker, los devs pueden usar `docker compose up postgres qdrant` solamente.
- Alinear `DATABASE_URL` del contenedor `api` con host `postgres` y credenciales del compose.
- Qdrant gRPC 6334 vs REST 6333: documentar cuál usa el cliente.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 Compose validado con `docker compose config`
- [ ] #2 Smoke manual documentado (comandos exactos) en notas de la tarea o README (task-63 puede consolidar)
- [ ] #3 Sin secretos hardcodeados en YAML (usar env_file / variables)
<!-- DOD:END -->
