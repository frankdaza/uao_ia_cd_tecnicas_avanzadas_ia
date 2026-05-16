---
id: TASK-85
title: Auditoria previa de imports y referencias para migracion clean-enough M2
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-16 16:49'
updated_date: '2026-05-16 16:50'
labels:
  - migracion
  - clean-architecture
  - modulo-2
  - auditoria
  - documentacion
dependencies: []
references:
  - src/rag/
  - src/qa/
  - src/app/
  - scripts/
  - tests/
  - backlog/docs/doc-005 - Auditoria-Imports-Migracion-Clean-Architecture.md
documentation:
  - >-
    backlog/decisions/decision-6 -
    Migracion-Incremental-Clean-Architecture-M2.md
  - backlog/docs/doc-004 - Estudio-Migracion-Clean-Architecture.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: high
ordinal: 85000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El ADR decision-6 adopta migracion incremental clean enough (Opcion A de doc-004). Antes de mover modulos, hace falta un inventario reproducible de dependencias para evitar reorganizacion a medias.

## Objetivo

Producir un informe unico en backlog/docs/ que liste quien importa `src.rag`, `src.qa` y `src.app`, con banderas de riesgo (ciclos, imports indirectos, scripts fuera de `src/`).

## Ejemplos de comandos (documentar salida en doc-005)

```bash
rg "from src\\.rag|import src\\.rag" --glob '!**/.git/**'
rg "from src\\.qa|import src\\.qa" --glob '!**/.git/**'
rg "from src\\.app|import src\\.app" --glob '!**/.git/**'
uv run pytest
```

## Fuera de alcance

Mover archivos, renombrar paquetes o tocar el grafo LangGraph.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Existe backlog/docs/doc-005 - Auditoria-Imports-Migracion-Clean-Architecture.md con front matter YAML valido (id doc-005, title, type, created_date).
- [ ] #2 El documento incluye tablas modulo-consumidor para imports hacia src/rag, src/qa y src/app (codigo, tests, scripts, notebooks, CI si aplica).
- [ ] #3 Se documentan comandos de busqueda reproducibles (rg) y resultados resumidos o pegados en anexo corto.
- [ ] #4 Se ejecuta uv run pytest en la rama y se registra el resultado baseline (passed/failed y alcance si es parcial).
- [ ] #5 No se modifica codigo de produccion ni tests salvo correcciones triviales de typos en doc; el foco es inventario.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer decision-6 y doc-004 para alinear criterios de clasificacion (nucleo M2 vs laboratorio).
2. Ejecutar busquedas rg documentadas; agrupar por consumidor (src/agentes, src/api, scripts, tests, notebooks).
3. Crear doc-005 con tablas y enlaces a archivos representativos (rutas relativas al repo).
4. Ejecutar `uv run pytest` y registrar conteo/resumen en doc-005.
5. Revisar con par (opcional) y dejar la tarea lista para ejecutar task-86 sin sorpresas.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Convencion de identificadores Python: espanol ASCII en nombres de simbolos; doc en espanol latinoamericano.
- doc-005 debe seguir backlog-docs-format (ver skill backlog-docs): nombre `doc-005 - Auditoria-Imports-Migracion-Clean-Architecture.md` y front matter con id/title/type/created_date.
- Si pytest baseline falla por entorno local, documentar el error y el comando exacto; no bloquear la auditoria pero marcar riesgo para task-86.
- Incluir en el informe una seccion "Riesgos para task-86" (imports dinamicos, string paths, pyproject packages).
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Al cierre: status Done sin task_complete ni mover a completed/ salvo pedido explicito.
- [ ] #2 Sin secretos ni API keys en el documento doc-005 ni en esta tarea.
<!-- DOD:END -->
