---
id: TASK-116
title: doc-004 Arquitectura M3 TAAM y evolución M2→proyecto-2 (informe + diagramas)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
updated_date: '2026-05-22 00:58'
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
  - >-
    backlog/decisions/decision-7 -
    Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - backlog/docs/usecases/GUION-DEMO-TAAM.md
  - proyecto-2/docker-compose.yml
  - proyecto-2/README.md
  - proyecto-2/scripts/verificar_stack_m3.sh
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Entregable de **documentación técnica (~10 %)** del taller M3 (milestone [m-0](backlog/milestones/m-0%20-%20agentic-final-project.md)): un informe de arquitectura que un evaluador pueda leer **sin abrir el código**, con diagramas alineados al **runtime real** de `proyecto-2/` tras TASK-114 (demo, webhook Telegram, tests de integración).

**Dependencias:** TASK-114 (semilla y guion demo) y TASK-96 (esqueleto `proyecto-2`). El código M2 productivo permanece en `proyecto-1/`; no mezclar runtimes.

## Objetivo

Publicar **`backlog/docs/doc-004 - Arquitectura-M3-Bot-Posoperatorio-TAAM.md`** como guía operativa del MVP TAAM (paralela a [doc-003](backlog/docs/doc-003%20-%20Arquitectura-Agente-Modulo-2.md) para M2).

## Renumeración previa (obligatoria)

El identificador **`doc-004` ya estaba ocupado** por [Estudio migración Clean Architecture](backlog/docs/doc-004%20-%20Estudio-Migracion-Clean-Architecture.md) (M2). Antes de crear el informe TAAM:

1. Renombrar ese estudio a **`doc-006 - Estudio-Migracion-Clean-Architecture.md`** (`id: doc-006`).
2. Actualizar enlaces en doc-003, doc-005, decision-6 y decision-7 (no reescribir tareas en `backlog/completed/` salvo enlace roto crítico).

## Contenido mínimo del doc-004 TAAM

| Sección | Contenido |
| --- | --- |
| 1. Resumen | Problema FVL, solución MVP, canal Telegram vía 2 |
| 2. Evolución M2→M3 | Tabla comparativa `proyecto-1` vs `proyecto-2` (agente, API, memoria, RAG, auth, puertos) |
| 3. Diagramas | ≥2 diagramas Mermaid: flujo paciente (webhook→`/chat`→agente) y despliegue Docker con **puertos reales** (`8001`, `15433`, `6334`, `5174`) |
| 4. Rubrica LangChain | Matriz componente → ruta en repo → comando `scripts/verificar_stack_m3.sh` |
| 5. UC-MVP | Tabla de los **5** UC con endpoints/rutas clave |
| 6. Referencias | [decision-7](backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md), [decision-4](backlog/decisions/decision-4%20-%20Payload-Qdrant-enriquecido-y-chunking-Markdown.md) (solo ingesta/payload), UC TAAM, [GUION-DEMO-TAAM](backlog/docs/usecases/GUION-DEMO-TAAM.md) |
| 7. Límites MVP | Fase 2 del UC (email, multimedia, RBAC completo, N8N/WhatsApp explícitamente fuera) |
| 8. Bonus t-SNE | Una nota: **no implementado** en el repo (opcional del curso) |
| 9. Informe PDF | Outline breve para sección M3 en informe del curso (sin obligar LaTeX en esta tarea) |

## Fallas a evitar

- Diagrama con puertos de M2 (`8000`, `15432`, `6333`) aplicados a TAAM.
- Afirmar que **decision-4** es el ADR de arquitectura M3 (es payload Qdrant M2; arquitectura TAAM = **decision-7**).
- Mencionar N8N, WhatsApp o polling Telegram como parte del producto.
- Omitir `session_id` canónico `telegram:{chat_id}` y tabla `vinculos_telegram`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 Existe `backlog/docs/doc-004 - Arquitectura-M3-Bot-Posoperatorio-TAAM.md` con front matter válido (`id: doc-004`, `title`, `type: architecture`, `created_date`)
- [x] #2 #2 El estudio Clean Architecture M2 quedó en `doc-006` y los enlaces activos en doc-003/doc-005/decision-6 apuntan a doc-006
- [x] #3 #3 Incluye ≥2 diagramas Mermaid y tabla comparativa proyecto-1 (M2) vs proyecto-2 (TAAM) con API, memoria, RAG, auth y puertos
- [x] #4 #4 Diagrama de despliegue usa puertos TAAM reales (8001, 15433, 6334) y ruta webhook `POST /api/integracion/telegram/webhook`
- [x] #5 #5 Matriz rubrica LangChain (Ruta A) con rutas bajo `proyecto-2/src/` y referencia a `scripts/verificar_stack_m3.sh`
- [x] #6 #6 Enlaza decision-7, decision-4 (alcance ingesta), los 5 UC-MVP del documento de casos de uso y GUION-DEMO-TAAM
- [x] #7 #7 Sección explícita de limitaciones MVP y trabajo futuro (Fase 2); nota t-SNE «no implementado»
- [x] #8 #8 `backlog/milestones/m-0` y `proyecto-2/README.md` enlazan doc-004
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Inventario:** leer `proyecto-2/docker-compose.yml`, `README.md`, `decision-7`, UC TAAM, `GUION-DEMO-TAAM.md`; ejecutar `./scripts/verificar_stack_m3.sh`.
2. **Renumerar doc-004 legacy → doc-006:** mover archivo, actualizar front matter `id`/`title`, enlaces en doc-003, doc-005, decision-6, decision-7.
3. **Redactar doc-004 TAAM:** front matter `type: architecture`, `modulo: 3`; secciones 1–9; diagramas Mermaid validados contra código.
4. **Enlaces de descubrimiento:** añadir doc-004 en `backlog/milestones/m-0` y sección «Documentación» en `proyecto-2/README.md`.
5. **Outline informe:** párrafo o subsección «Informe del curso» con bullets (sin crear PDF salvo que el usuario lo pida).
6. **Cierre Backlog:** marcar AC y DoD; `task_edit` status Done; `finalSummary` breve.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- **ADR M3:** decision-7 (no decision-4).
- **decision-4:** solo patrón de payload/chunking reutilizado en ingesta PDF TAAM.
- **Puertos TAAM (compose):** API 8001, Postgres host 15433, Qdrant REST 6334, gRPC 6335, Vite 5174.
- **Verificación rubrica:** `cd proyecto-2 && ./scripts/verificar_stack_m3.sh` (exit 0 al cierre de TASK-116).
- **t-SNE:** no hay notebook ni artefacto en repo; documentar como «no aplicado».
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se renumeró el estudio Clean Architecture M2 a doc-006 y se publicó doc-004 — Arquitectura-M3-Bot-Posoperatorio-TAAM.md con comparativa M2/M3, tres diagramas Mermaid (secuencia paciente, panel staff, Docker con puertos 8001/15433/6334/5174), matriz rubrica LangChain + verificar_stack_m3.sh, trazabilidad 5 UC-MVP, límites Fase 2, nota t-SNE no implementado y outline informe. Enlaces en m-0, proyecto-2/README, decision-7 y docs M2 (doc-003, doc-005, decision-6).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Revisión cruzada: ningún diagrama del doc-004 contradice `proyecto-2/docker-compose.yml` ni `README.md`
- [x] #2 Sin secretos ni tokens en el markdown del doc
- [x] #3 Enlaces relativos válidos a decision-7, UC TAAM y GUION desde `backlog/docs/`
<!-- DOD:END -->
